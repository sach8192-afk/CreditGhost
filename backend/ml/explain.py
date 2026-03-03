# ═══════════════════════════════════════════════════════════════
# CreditGhost — Smart Explainer (explain.py)
# ═══════════════════════════════════════════════════════════════
#
# WHAT THIS FILE DOES:
#
# score_engine.py  → Credit Score (300-900)
# train.py         → Trust Score (0-100)
# explain.py       → WHY those scores, with real evidence
#
# WHY NOT TRADITIONAL SHAP?
# SHAP estimates feature importance using averages.
# Our explanations read ACTUAL transactions and give
# REAL evidence with REAL point values.
#
# "You recharged 3/3 months → +28 pts" is more honest
# than "recharge_consistency SHAP value = 0.34"
#
# FRONTEND INTEGRATION:
# One button "Why this score?" on result page
# Calls GET /explain/{persona} or POST /explain
# Returns structured JSON → renders explanation cards
#
# Run: python ml/explain.py
# ═══════════════════════════════════════════════════════════════

import json
import os
import sys
from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.score_engine import (
    calculate_credit_score,
    get_monthly_income,
    get_monthly_spend,
    get_balance_history,
    group_by_month,
    coefficient_of_variation,
    safe_mean,
    is_telecom,
    is_utility,
    is_emi,
    is_successful_debit,
    is_failed,
    get_transaction_hour,
    clamp,
    SIGNAL_WEIGHTS,
)


# ═══════════════════════════════════════════════════════════════
# SECTION 1 — TRANSACTION EVIDENCE EXTRACTORS
#
# Each function below reads raw transactions and returns
# a list of SPECIFIC evidence strings like:
# "Recharged Jio ₹199 on 3 out of 3 months"
# "Balance dropped to ₹180 in January 2024"
#
# These are the exact strings shown on the frontend cards.
# Every string is derived from REAL transaction data.
# Nothing is estimated or made up.
# ═══════════════════════════════════════════════════════════════

def extract_income_evidence(transactions, signal_score, max_score):
    """
    Reads income transactions and returns evidence strings
    explaining the Income Stability signal score.
    """
    evidence     = []
    improvements = []

    monthly_groups = group_by_month(transactions)
    total_months   = max(len(monthly_groups), 1)
    monthly_income = get_monthly_income(transactions)

    if not monthly_income or max(monthly_income) == 0:
        evidence.append("No income transactions detected in 3 months")
        improvements.append("Link a bank account with salary or UPI income")
        return evidence, improvements

    avg_income         = safe_mean(monthly_income)
    months_with_income = sum(1 for m in monthly_income if m > 500)
    cv                 = coefficient_of_variation(monthly_income)

    # Evidence: income arrival
    if months_with_income == total_months:
        evidence.append(f"Income arrived in all {total_months} months ✓")
    else:
        missing = total_months - months_with_income
        evidence.append(
            f"Income missing in {missing} of {total_months} months"
        )
        improvements.append(
            f"Ensure income credit every month — currently missing {missing} month(s)"
        )

    # Evidence: average income amount
    evidence.append(f"Average monthly income: ₹{round(avg_income):,}")

    # Evidence: consistency
    if cv < 0.15:
        evidence.append(
            f"Very consistent income (varies only {round(cv*100)}%) ✓"
        )
    elif cv < 0.35:
        evidence.append(
            f"Moderate income variation ({round(cv*100)}% month-to-month)"
        )
        improvements.append(
            "More consistent income sources would add 15-25 pts"
        )
    else:
        evidence.append(
            f"High income variation ({round(cv*100)}%) — irregular earnings"
        )
        improvements.append(
            "Consistent monthly income, even if smaller, improves score significantly"
        )

    # Evidence: income trend
    if len(monthly_income) >= 3:
        if monthly_income[-1] > monthly_income[0] * 1.05:
            evidence.append("Income is growing month over month ✓")
        elif monthly_income[-1] < monthly_income[0] * 0.85:
            evidence.append("Income declined over the 3-month period")
            improvements.append("Stabilise income before reapplying")

    # Improvement if score is low
    pct = signal_score / max_score
    if pct < 0.5 and avg_income < 8000:
        improvements.append(
            f"Average monthly income of ₹{round(avg_income):,} is below ₹8,000 — "
            f"higher income adds up to 30 pts"
        )

    return evidence, improvements


def extract_payment_evidence(transactions, signal_score, max_score):
    """
    Reads telecom and utility transactions and returns evidence
    explaining the Payment Consistency signal score.
    """
    evidence     = []
    improvements = []

    monthly_groups = group_by_month(transactions)
    total_months   = max(len(monthly_groups), 1)

    # ── Recharge analysis ──────────────────────────────────────
    months_with_recharge = 0
    recharge_merchants   = []
    recharge_amounts     = []

    for month, txns in sorted(monthly_groups.items()):
        month_recharges = [
            t for t in txns
            if is_telecom(t) and is_successful_debit(t)
        ]
        if month_recharges:
            months_with_recharge += 1
            for r in month_recharges:
                recharge_merchants.append(r.get("merchantName", ""))
                recharge_amounts.append(r["amount"])

    if months_with_recharge == total_months:
        # Find most common recharge merchant
        merchant = max(
            set(recharge_merchants), key=recharge_merchants.count
        ) if recharge_merchants else "phone"
        evidence.append(
            f"Phone recharged {months_with_recharge}/{total_months} months ✓"
        )
        if recharge_amounts:
            avg_amt = round(safe_mean(recharge_amounts))
            evidence.append(f"Typical recharge amount: ₹{avg_amt}")
    elif months_with_recharge > 0:
        missed = total_months - months_with_recharge
        evidence.append(
            f"Phone recharged {months_with_recharge}/{total_months} months "
            f"({missed} month missed)"
        )
        improvements.append(
            f"Recharge every month without fail — adds ~25 pts instantly"
        )
    else:
        evidence.append("No phone recharge found in any month")
        improvements.append(
            "Set up monthly Jio/Airtel recharge — single biggest quick win"
        )

    # Recharge amount consistency
    if len(recharge_amounts) >= 2:
        cv = coefficient_of_variation(recharge_amounts)
        if cv < 0.10:
            evidence.append(
                f"Same recharge amount every month (₹{round(recharge_amounts[0])}) ✓"
            )
        elif cv > 0.40:
            evidence.append(
                "Recharge amount changes significantly each month"
            )
            improvements.append(
                "Pick one fixed recharge plan — consistency signals stable income"
            )

    # ── Utility bill analysis ──────────────────────────────────
    months_with_bills = 0
    bill_merchants    = []

    for month, txns in sorted(monthly_groups.items()):
        month_bills = [
            t for t in txns
            if is_utility(t) and is_successful_debit(t)
        ]
        if month_bills:
            months_with_bills += 1
            for b in month_bills:
                bill_merchants.append(b.get("merchantName", ""))

    if months_with_bills == total_months:
        evidence.append(
            f"Utility bills paid in all {total_months} months ✓"
        )
    elif months_with_bills > 0:
        evidence.append(
            f"Utility bills paid in {months_with_bills}/{total_months} months"
        )
        improvements.append(
            "Pay electricity/water bill every month — adds 15-20 pts"
        )
    else:
        evidence.append("No utility bill payments detected")
        improvements.append(
            "Pay bills via UPI — even one bill/month improves score"
        )

    return evidence, improvements


def extract_savings_evidence(transactions, signal_score, max_score):
    """
    Reads income vs spending and balance history to explain
    the Savings Discipline signal score.
    """
    evidence     = []
    improvements = []

    monthly_income  = get_monthly_income(transactions)
    monthly_spend   = get_monthly_spend(transactions)
    balance_history = get_balance_history(transactions)

    avg_income = safe_mean(monthly_income) if monthly_income else 0
    avg_spend  = safe_mean(monthly_spend)  if monthly_spend  else 0

    if avg_income == 0:
        evidence.append("Cannot calculate savings — no income detected")
        return evidence, improvements

    # Savings rate
    savings_rate = (avg_income - avg_spend) / avg_income
    savings_pct  = round(savings_rate * 100, 1)

    if savings_rate >= 0.20:
        evidence.append(f"Saving {savings_pct}% of income every month ✓")
    elif savings_rate >= 0.08:
        evidence.append(f"Saving {savings_pct}% of monthly income")
        improvements.append(
            f"Increase savings to 15% for +20 pts "
            f"(currently ₹{round(avg_income*savings_rate):,}/month)"
        )
    elif savings_rate >= 0:
        evidence.append(
            f"Saving only {savings_pct}% of income "
            f"(₹{round(avg_income*savings_rate):,}/month)"
        )
        improvements.append(
            f"Save ₹{round(avg_income*0.10):,}/month (10% of income) → +30 pts"
        )
    else:
        evidence.append(
            f"Spending ₹{round(abs(avg_income*savings_rate)):,} MORE than earning monthly"
        )
        improvements.append(
            "Reduce monthly spending below income level — critical for score"
        )

    # Per month savings consistency
    if monthly_income and monthly_spend:
        months_saving = sum(
            1 for i in range(min(len(monthly_income), len(monthly_spend)))
            if monthly_income[i] > monthly_spend[i] * 1.03
        )
        total_months = min(len(monthly_income), len(monthly_spend))
        if months_saving == total_months:
            evidence.append(f"Saved money in all {total_months} months ✓")
        elif months_saving > 0:
            evidence.append(
                f"Saved money in {months_saving} of {total_months} months"
            )

    # Balance cushion
    if balance_history:
        min_bal = min(balance_history)
        avg_bal = round(safe_mean(balance_history))

        if min_bal >= 2000:
            evidence.append(
                f"Balance never dropped below ₹{round(min_bal):,} ✓"
            )
        elif min_bal >= 0:
            evidence.append(
                f"Balance touched ₹{round(min_bal):,} at lowest point"
            )
            if min_bal < 200:
                improvements.append(
                    "Maintain minimum ₹500 balance at all times → +15 pts"
                )
        else:
            evidence.append(
                f"Balance went negative (₹{round(min_bal):,}) — overdraft detected"
            )
            improvements.append(
                "Avoid overdraft completely — negative balance loses 20+ pts"
            )

    return evidence, improvements


def extract_spending_evidence(transactions, signal_score, max_score):
    """
    Reads monthly spending patterns and night transactions
    to explain the Spending Behavior signal score.
    """
    evidence     = []
    improvements = []

    monthly_spend = get_monthly_spend(transactions)
    total_txns    = len(transactions)

    if not monthly_spend or safe_mean(monthly_spend) == 0:
        evidence.append("Insufficient spending data")
        return evidence, improvements

    avg_spend = safe_mean(monthly_spend)
    cv        = coefficient_of_variation(monthly_spend)

    # Spending consistency
    if cv < 0.15:
        evidence.append(
            f"Very consistent spending each month (varies {round(cv*100)}%) ✓"
        )
    elif cv < 0.30:
        evidence.append(
            f"Spending varies {round(cv*100)}% month-to-month — moderate"
        )
    else:
        evidence.append(
            f"Spending varies {round(cv*100)}% — significant inconsistency"
        )
        improvements.append(
            "Smooth out spending across months — spikes lose 15+ pts"
        )

    # Spike detection
    spike_months = [
        i+1 for i, s in enumerate(monthly_spend)
        if s > avg_spend * 2.0
    ]
    if spike_months:
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        evidence.append(
            f"Spending spike detected in month {spike_months[0]} "
            f"(more than 2x normal)"
        )
        improvements.append(
            "Avoid large one-off purchases — single spike loses 20 pts"
        )
    else:
        evidence.append("No unusual spending spikes detected ✓")

    # Night transactions
    if total_txns > 0:
        night_txns = sum(
            1 for t in transactions
            if get_transaction_hour(t) >= 23
            or get_transaction_hour(t) <= 4
        )
        night_pct = round(night_txns / total_txns * 100)

        if night_pct <= 5:
            evidence.append(
                f"Only {night_pct}% transactions at night — healthy pattern ✓"
            )
        elif night_pct <= 15:
            evidence.append(
                f"{night_pct}% of transactions happen between 11PM-5AM"
            )
        else:
            evidence.append(
                f"{night_pct}% transactions at night — high late-night activity"
            )
            improvements.append(
                "High night transactions signal risky behavior — loses 10+ pts"
            )

    return evidence, improvements


def extract_frequency_evidence(transactions, signal_score, max_score):
    """
    Reads transaction counts and categories to explain
    the Transaction Frequency signal score.
    """
    evidence     = []
    improvements = []

    monthly_groups = group_by_month(transactions)
    total_months   = max(len(monthly_groups), 1)
    total_txns     = len(transactions)
    avg_per_month  = round(total_txns / total_months, 1)

    # Volume
    if avg_per_month >= 30:
        evidence.append(
            f"Very active: {avg_per_month} UPI transactions/month ✓"
        )
    elif avg_per_month >= 15:
        evidence.append(
            f"{avg_per_month} UPI transactions per month — good activity"
        )
    else:
        evidence.append(
            f"Only {avg_per_month} UPI transactions/month — low activity"
        )
        improvements.append(
            "Pay more daily expenses via UPI (grocery, transport, food) → +20 pts"
        )

    # Merchant diversity
    unique_categories = len(set(
        t.get("merchantCategory", "OTHERS") for t in transactions
    ))
    unique_merchants = len(set(
        t.get("merchantName", "") for t in transactions
    ))

    if unique_categories >= 6:
        evidence.append(
            f"Spending across {unique_categories} categories — "
            f"diverse financial life ✓"
        )
    else:
        evidence.append(
            f"Spending only in {unique_categories} categories — limited diversity"
        )
        improvements.append(
            "Use UPI across more categories (transport, grocery, health) → +10 pts"
        )

    evidence.append(f"{unique_merchants} unique merchants over 3 months")

    # Failed transactions
    failed_count = sum(1 for t in transactions if is_failed(t))
    failed_pct   = round(failed_count / total_txns * 100) if total_txns else 0

    if failed_pct == 0:
        evidence.append("Zero failed transactions ✓")
    elif failed_pct <= 5:
        evidence.append(f"{failed_pct}% transactions failed — acceptable")
    elif failed_pct <= 15:
        evidence.append(
            f"{failed_pct}% transactions failed ({failed_count} payments bounced)"
        )
        improvements.append(
            f"Reduce failed payments — {failed_count} bounced payments loses 10 pts"
        )
    else:
        evidence.append(
            f"{failed_pct}% transactions failed — indicates low balance"
        )
        improvements.append(
            "Maintain buffer balance to prevent payment failures → +15 pts"
        )

    return evidence, improvements


def extract_debt_evidence(transactions, signal_score, max_score):
    """
    Reads EMI and balance data to explain
    the Debt Signals score.
    """
    evidence     = []
    improvements = []

    monthly_groups  = group_by_month(transactions)
    total_months    = max(len(monthly_groups), 1)
    monthly_income  = get_monthly_income(transactions)
    balance_history = get_balance_history(transactions)
    avg_income      = safe_mean(monthly_income) if monthly_income else 0

    # EMI detection
    all_emi_txns = [
        t for t in transactions
        if is_emi(t) and is_successful_debit(t)
    ]

    if not all_emi_txns:
        evidence.append("No existing EMI or loan payments detected ✓")
    else:
        # Monthly EMI amounts
        monthly_emi = defaultdict(float)
        for t in all_emi_txns:
            month = t["date"][:7]
            monthly_emi[month] += t["amount"]

        avg_emi   = safe_mean(list(monthly_emi.values()))
        emi_ratio = avg_emi / avg_income if avg_income > 0 else 0

        # List unique EMI merchants
        emi_merchants = list(set(
            t.get("merchantName", "Loan") for t in all_emi_txns
        ))[:3]

        evidence.append(
            f"Active EMI payments: {', '.join(emi_merchants)}"
        )
        evidence.append(
            f"Average monthly EMI: ₹{round(avg_emi):,} "
            f"({round(emi_ratio*100)}% of income)"
        )

        if emi_ratio <= 0.25:
            evidence.append("EMI burden is manageable (under 25%) ✓")
        elif emi_ratio <= 0.40:
            evidence.append(
                f"EMI is {round(emi_ratio*100)}% of income — moderate burden"
            )
            improvements.append(
                "Reduce EMI burden below 30% before taking new loans"
            )
        else:
            evidence.append(
                f"EMI is {round(emi_ratio*100)}% of income — high burden"
            )
            improvements.append(
                f"EMI ratio {round(emi_ratio*100)}% is too high — "
                f"repay existing loans first → +25 pts"
            )

    # Overdraft/negative balance
    if balance_history:
        min_bal      = min(balance_history)
        went_negative = min_bal < 0

        if went_negative:
            evidence.append(
                f"Account balance went negative (₹{round(min_bal):,}) — overdraft"
            )
            improvements.append(
                "Avoid overdraft — negative balance is biggest trust killer"
            )
        else:
            min_positive = min(b for b in balance_history if b >= 0)
            if min_positive < 100:
                evidence.append(
                    "Balance came very close to zero — financial stress signal"
                )
                improvements.append(
                    "Keep at least ₹500 minimum balance at all times"
                )
            else:
                evidence.append(
                    f"Balance stayed positive throughout (min ₹{round(min_bal):,}) ✓"
                )

    return evidence, improvements


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — SIGNAL METADATA
# Display names, icons, and context for each signal
# Used to build the frontend explanation cards
# ═══════════════════════════════════════════════════════════════

SIGNAL_META = {
    "income_stability": {
        "display_name": "Income Stability",
        "icon":         "💰",
        "what_it_means":"How consistently and sufficiently money comes in",
        "why_it_matters":"Regular income = ability to repay loan on time",
        "extractor":    extract_income_evidence,
    },
    "payment_consistency": {
        "display_name": "Payment Consistency",
        "icon":         "📱",
        "what_it_means":"Whether bills and recharges are paid every month",
        "why_it_matters":"Paying ₹199 Jio every month predicts loan repayment",
        "extractor":    extract_payment_evidence,
    },
    "savings_discipline": {
        "display_name": "Savings Discipline",
        "icon":         "🏦",
        "what_it_means":"Whether money is saved after expenses each month",
        "why_it_matters":"Self-control with savings = self-control with EMIs",
        "extractor":    extract_savings_evidence,
    },
    "spending_behavior": {
        "display_name": "Spending Behavior",
        "icon":         "🛒",
        "what_it_means":"Whether spending is consistent or erratic",
        "why_it_matters":"Predictable spending = predictable person = safer loan",
        "extractor":    extract_spending_evidence,
    },
    "transaction_frequency": {
        "display_name": "Transaction Activity",
        "icon":         "📊",
        "what_it_means":"How actively UPI is used across different merchants",
        "why_it_matters":"Active digital footprint = more data = better assessment",
        "extractor":    extract_frequency_evidence,
    },
    "debt_signals": {
        "display_name": "Debt Burden",
        "icon":         "⚖️",
        "what_it_means":"Existing loans and their burden on monthly income",
        "why_it_matters":"Too much existing debt = can't handle new loan",
        "extractor":    extract_debt_evidence,
    },
}


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — MASTER EXPLAIN FUNCTION
#
# THIS IS WHAT score.py CALLS when frontend clicks
# the "Why this score?" button.
#
# Input:  AA JSON (one user's bank data)
# Output: structured explanation JSON ready for frontend
# ═══════════════════════════════════════════════════════════════

def generate_explanation(aa_json):
    """
    THE MAIN FUNCTION called by score.py.

    Reads AA JSON → runs score engine → extracts evidence
    from each signal → returns complete explanation.

    Frontend receives this and renders explanation cards.
    """
    transactions = aa_json.get("transactions", [])

    if not transactions:
        return {"error": "No transactions to explain"}

    # Step 1: Run score engine to get signal breakdown
    score_result = calculate_credit_score(aa_json)

    if "error" in score_result:
        return {"error": score_result["error"]}

    final_score = score_result["final_score"]
    bucket      = score_result["bucket"]
    breakdown   = score_result["breakdown"]

    # Step 2: Build explanation for each signal
    signal_explanations = []

    for signal_name, meta in SIGNAL_META.items():

        signal_data  = breakdown.get(signal_name, {})
        signal_score = signal_data.get("score", 0)
        max_score    = signal_data.get("max", SIGNAL_WEIGHTS[signal_name])
        pct          = round(signal_score / max_score * 100) if max_score else 0

        # Direction: helping if above 65%, hurting if below
        direction = "helping" if pct >= 65 else "hurting"

        # Impact points relative to midpoint (50%)
        midpoint   = max_score * 0.50
        impact_pts = round(signal_score - midpoint)

        # Get level label
        if pct >= 85:   level = "Excellent"
        elif pct >= 65: level = "Good"
        elif pct >= 40: level = "Fair"
        else:           level = "Poor"

        # Generate evidence strings from real transactions
        extractor = meta["extractor"]
        evidence, improvements = extractor(
            transactions, signal_score, max_score
        )

        # Build headline based on score
        headlines = {
            "Excellent": f"Strong {meta['display_name'].lower()} — top tier",
            "Good":      f"Good {meta['display_name'].lower()} — above average",
            "Fair":      f"Average {meta['display_name'].lower()} — room to grow",
            "Poor":      f"Weak {meta['display_name'].lower()} — needs attention",
        }
        headline = headlines[level]

        signal_explanations.append({
            "signal":        signal_name,
            "name":          meta["display_name"],
            "icon":          meta["icon"],
            "what_it_means": meta["what_it_means"],
            "why_it_matters":meta["why_it_matters"],
            "score":         signal_score,
            "max":           max_score,
            "pct":           pct,
            "level":         level,
            "direction":     direction,
            "impact_pts":    impact_pts,
            "headline":      headline,
            "evidence":      evidence,
            "improvements":  improvements[:2],  # max 2 tips per signal
        })

    # Step 3: Sort — worst hurting first, then best helping
    signal_explanations.sort(key=lambda x: x["pct"])

    helping  = [e for e in signal_explanations if e["direction"] == "helping"]
    hurting  = [e for e in signal_explanations if e["direction"] == "hurting"]

    # Step 4: Top improvements across all signals
    all_improvements = []
    for exp in signal_explanations:
        for tip in exp["improvements"]:
            all_improvements.append({
                "signal": exp["name"],
                "icon":   exp["icon"],
                "tip":    tip,
            })

    # Sort improvements by signal pct (fix worst first)
    all_improvements = all_improvements[:4]

    # Step 5: Score narrative — one sentence summary
    if final_score >= 750:
        narrative = (
            f"Excellent financial behavior across most signals. "
            f"Very likely to repay a microfinance loan on time."
        )
    elif final_score >= 600:
        narrative = (
            f"Good financial habits with some areas to improve. "
            f"Suitable for microfinance loans with standard terms."
        )
    elif final_score >= 450:
        narrative = (
            f"Mixed financial signals detected. "
            f"Loan possible with smaller amount or co-applicant."
        )
    else:
        narrative = (
            f"Several high-risk signals detected. "
            f"Improving payment consistency and savings would help significantly."
        )

    # Step 6: Build complete response
    return {
        # Summary
        "final_score":   final_score,
        "bucket":        bucket,
        "narrative":     narrative,

        # All 6 signals sorted worst to best
        "all_signals":   signal_explanations,

        # Separated for frontend card layout
        "helping":       helping,    # green cards
        "hurting":       hurting,    # red cards

        # Top action items for "How to improve" section
        "top_improvements": all_improvements,

        # Raw signal scores for the chart
        "signal_chart": [
            {
                "name":  e["name"],
                "icon":  e["icon"],
                "score": e["score"],
                "max":   e["max"],
                "pct":   e["pct"],
                "color": "#16a34a" if e["direction"] == "helping"
                         else "#dc2626",
            }
            for e in signal_explanations
        ],

        "transactions_analysed": len(transactions),
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — SAVE EXPLANATIONS FOR DEMO PERSONAS
# Pre-generates explanations for Ramesh, Priya, Arjun
# So the demo button is instant — no calculation delay
# ═══════════════════════════════════════════════════════════════

def pregenerate_demo_explanations():
    """
    Pre-generates explanations for all 3 demo personas.
    Saves to ml/data/demo_explanations.json
    score.py loads this at startup for instant demo.
    """
    try:
        with open("ml/data/demo_personas.json") as f:
            personas = json.load(f)
    except FileNotFoundError:
        print("  ❌ demo_personas.json not found")
        print("     Run: python ml/generate_data.py first")
        return None

    demo_explanations = {}

    for name, aa_json in personas.items():
        if aa_json is None:
            print(f"  ⚠️  {name}: No data, skipping")
            continue

        print(f"  Generating explanation for {name}...")
        explanation = generate_explanation(aa_json)
        demo_explanations[name] = explanation

    # Save
    os.makedirs("ml/data", exist_ok=True)
    output_path = "ml/data/demo_explanations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(demo_explanations, f, indent=2, ensure_ascii=False)

    print(f"  💾 Saved: {output_path}")
    return demo_explanations


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — PRETTY PRINT FOR TERMINAL TESTING
# ═══════════════════════════════════════════════════════════════

def print_explanation(name, explanation):
    """Prints explanation in a readable terminal format."""

    if "error" in explanation:
        print(f"  ❌ Error: {explanation['error']}")
        return

    print(f"\n{'═'*60}")
    print(f"  👤 {name.upper()}")
    print(f"  Score: {explanation['final_score']} — {explanation['bucket']}")
    print(f"  {explanation['narrative']}")
    print(f"{'═'*60}")

    # Helping signals
    print(f"\n  ✅ WHAT'S HELPING YOUR SCORE:")
    for exp in explanation["helping"]:
        bar = "█" * (exp["pct"] // 10) + "░" * (10 - exp["pct"] // 10)
        print(f"\n  {exp['icon']} {exp['name']}")
        print(f"     {bar}  {exp['score']}/{exp['max']} pts ({exp['pct']}%)")
        print(f"     {exp['headline']}")
        for e in exp["evidence"]:
            print(f"       • {e}")

    # Hurting signals
    print(f"\n  ❌ WHAT'S HURTING YOUR SCORE:")
    for exp in explanation["hurting"]:
        bar = "█" * (exp["pct"] // 10) + "░" * (10 - exp["pct"] // 10)
        print(f"\n  {exp['icon']} {exp['name']}")
        print(f"     {bar}  {exp['score']}/{exp['max']} pts ({exp['pct']}%)")
        print(f"     {exp['headline']}")
        for e in exp["evidence"]:
            print(f"       • {e}")
        for tip in exp["improvements"]:
            print(f"       💡 {tip}")

    # Top improvements
    if explanation["top_improvements"]:
        print(f"\n  🎯 TOP ACTIONS TO IMPROVE SCORE:")
        for i, tip in enumerate(explanation["top_improvements"], 1):
            print(f"  {i}. {tip['icon']} {tip['tip']}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("=" * 60)
    print("  CREDITGHOST — SMART EXPLAINER")
    print("  Real evidence from real transactions")
    print("=" * 60)

    # Load demo personas
    try:
        with open("ml/data/demo_personas.json") as f:
            personas = json.load(f)
        print(f"\n  ✅ Loaded 3 demo personas")
    except FileNotFoundError:
        print("  ❌ demo_personas.json not found")
        print("     Run: python ml/generate_data.py first")
        exit(1)

    # Generate and print explanation for each persona
    for name, aa_json in personas.items():
        if aa_json is None:
            print(f"\n  ⚠️  {name}: No data available")
            continue
        explanation = generate_explanation(aa_json)
        print_explanation(name, explanation)

    # Pre-generate and save for demo
    print(f"\n{'─'*60}")
    print("  Saving pre-generated explanations...")
    pregenerate_demo_explanations()

    print(f"\n{'='*60}")
    print("  ✅ COMPLETE")
    print(f"  Saved: ml/data/demo_explanations.json")
    print(f"\n  Frontend button 'Why this score?' calls:")
    print(f"  GET  /explain/ramesh  → instant pre-generated")
    print(f"  POST /explain         → real-time for live user")
    print(f"{'='*60}")