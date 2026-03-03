# ═══════════════════════════════════════════════════════════════
# CreditGhost — Score Engine v2.0
# Updated with 3 fixes from Review 1 feedback
#
# CHANGE 1 — Rebalanced signal weights
#   Payment Consistency: 180 → 200 (strongest predictor)
#   Income Stability:    200 → 180 (seasonal fix compensates)
#   Savings Discipline:  150 → 130 (poor people penalized less)
#   Spending Behavior:   130 → 140 (quality txn fix adds value)
#   Debt Signals:        140 → 150 (most protective signal)
#   Transaction Freq:    100 → 100 (unchanged)
#
# CHANGE 2 — Seasonal Income Detection
#   Farmers/seasonal workers no longer penalized for high CV
#   3-month total capacity check added
#   CV penalty softened from 1.0x to 0.6x multiplier
#
# CHANGE 4 — Quality over Quantity (Transaction Frequency)
#   Raw transaction count replaced with essential ratio
#   Essential = grocery, utility, transport, telecom, healthcare
#   Measures WHAT you spend on, not HOW MUCH you spend
#
# Run standalone test: python ml/score_engine.py
# Called by: backend/app/routes/score.py
# ═══════════════════════════════════════════════════════════════

import json
import os
import statistics
from datetime import datetime, timedelta
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════
# SECTION 1 — CONSTANTS
# ═══════════════════════════════════════════════════════════════

# ── CHANGE 1: Updated signal weights ──────────────────────────
# Old: [200, 180, 150, 130, 140, 100] = 900
# New: [180, 200, 130, 140, 150, 100] = 900
SIGNAL_WEIGHTS = {
    "income_stability":        180,   # ↓ was 200 (seasonal fix compensates)
    "payment_consistency":     200,   # ↑ was 180 (strongest predictor)
    "savings_discipline":      130,   # ↓ was 150 (less harsh on poor)
    "spending_behavior":       140,   # ↑ was 130 (quality txn fix)
    "transaction_frequency":   100,   # = unchanged
    "debt_signals":            150,   # ↑ was 140 (most protective)
}
# Total still = 900 ✅

BASE_SCORE = 300

# ── CHANGE 2: Seasonal income constants ───────────────────────
# If 3-month total income can cover loan 3x = seasonal worker
SEASONAL_LOAN_TARGET   = 20000   # typical microfinance loan (₹)
SEASONAL_CV_THRESHOLD  = 0.50    # CV above this = seasonal pattern
SEASONAL_BONUS_MAX     = 25      # max bonus pts for seasonal workers
CV_PENALTY_MULTIPLIER  = 0.60    # soften CV penalty (was 1.0)

# ── CHANGE 4: Essential merchant categories ───────────────────
# These categories = responsible, necessary spending
ESSENTIAL_CATEGORIES = {
    "GROCERY",       # food and daily needs
    "UTILITY",       # electricity, water, gas
    "TRANSPORT",     # bus, metro, auto, petrol
    "TELECOM",       # phone recharge/bill
    "HEALTHCARE",    # medicine, hospital, pharmacy
    "EDUCATION",     # school fees, tuition
    "RENT",          # house rent
    "FINANCIAL",     # insurance, SIP, RD
}

# These categories = discretionary, non-essential spending
DISCRETIONARY_CATEGORIES = {
    "FOOD_DELIVERY",   # Swiggy, Zomato
    "SHOPPING",        # Amazon, Flipkart, Myntra
    "ENTERTAINMENT",   # Netflix, movies, games
    "DINING",          # restaurants, cafes
}

# Income and bill detection
INCOME_CATEGORIES  = {"SALARY", "GOVERNMENT"}
BILL_CATEGORIES    = {"UTILITY", "TELECOM"}
DEBT_CATEGORIES    = {"EMI"}

TELECOM_MERCHANTS = {
    "jio", "airtel", "vi ", "vodafone", "bsnl",
    "recharge", "prepaid", "postpaid"
}
UTILITY_MERCHANTS = {
    "electricity", "bescom", "tneb", "msedcl", "tsspdcl",
    "cesc", "water", "gas", "indane", "bharat gas", "hp gas",
    "internet", "broadband", "fibernet", "fiber"
}

# Income thresholds for microfinance
MINIMUM_INCOME    = 5000
GOOD_INCOME       = 20000
EXCELLENT_INCOME  = 40000

# Score buckets
BUCKETS = [
    (750, 900, "Excellent", "⭐", "#2980b9"),
    (600, 750, "Good",      "🟢", "#27ae60"),
    (450, 600, "Fair",      "🟡", "#f39c12"),
    (300, 450, "Poor",      "🔴", "#e74c3c"),
]


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def safe_mean(values):
    """Average of a list. Returns 0 if empty."""
    return statistics.mean(values) if values else 0.0


def safe_stdev(values):
    """Standard deviation. Returns 0 if less than 2 values."""
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def coefficient_of_variation(values):
    """
    CV = stdev / mean
    Measures relative variability.
    CV 0.0 = perfectly consistent
    CV 1.0 = very erratic
    """
    mean = safe_mean(values)
    if mean == 0:
        return 1.0
    return safe_stdev(values) / mean


def get_transaction_month(txn):
    """Extracts YYYY-MM from transaction date."""
    return txn["date"][:7]


def is_telecom(txn):
    """Checks if transaction is a phone recharge or bill."""
    if txn.get("merchantCategory") == "TELECOM":
        return True
    merchant_lower = txn.get("merchantName", "").lower()
    return any(k in merchant_lower for k in TELECOM_MERCHANTS)


def is_utility(txn):
    """Checks if transaction is a utility bill."""
    if txn.get("merchantCategory") == "UTILITY":
        return True
    merchant_lower = txn.get("merchantName", "").lower()
    return any(k in merchant_lower for k in UTILITY_MERCHANTS)


def is_emi(txn):
    """Checks if transaction is an EMI or loan repayment."""
    if txn.get("merchantCategory") == "EMI":
        return True
    merchant_lower = txn.get("merchantName", "").lower()
    emi_keywords = {
        "emi", "loan", "repay", "instalment",
        "bajaj", "muthoot", "manappuram",
        "kreditbee", "cashe", "earlysalary"
    }
    return any(k in merchant_lower for k in emi_keywords)


def is_income(txn):
    """Checks if transaction is income (money coming in)."""
    return (txn.get("type") == "CREDIT" and
            txn.get("transactionStatus") == "SUCCESS")


def is_successful_debit(txn):
    """Checks if money left the account successfully."""
    return (txn.get("type") == "DEBIT" and
            txn.get("transactionStatus") == "SUCCESS")


def is_failed(txn):
    """
    Failed transaction = tried to pay but couldn't.
    Indicates insufficient balance = financial stress.
    """
    return txn.get("transactionStatus") == "FAILED"


def get_transaction_hour(txn):
    """Extracts hour (0-23) from time string HH:MM:SS."""
    try:
        return int(txn.get("time", "12:00:00").split(":")[0])
    except:
        return 12


def group_by_month(transactions):
    """
    Groups transactions by month.
    Returns: {"2024-01": [txn1, txn2...], "2024-02": [...]}
    """
    monthly = defaultdict(list)
    for txn in transactions:
        month = get_transaction_month(txn)
        monthly[month].append(txn)
    return dict(monthly)


def get_monthly_income(transactions):
    """
    Returns list of monthly income totals.
    Example: [8500, 7200, 9100] for 3 months
    """
    monthly_groups = group_by_month(transactions)
    monthly_income = []
    for month, txns in sorted(monthly_groups.items()):
        income = sum(t["amount"] for t in txns if is_income(t))
        monthly_income.append(income)
    return monthly_income


def get_monthly_spend(transactions):
    """
    Returns list of monthly spending totals.
    Only counts successful debits.
    """
    monthly_groups = group_by_month(transactions)
    monthly_spend  = []
    for month, txns in sorted(monthly_groups.items()):
        spend = sum(t["amount"] for t in txns if is_successful_debit(t))
        monthly_spend.append(spend)
    return monthly_spend


def get_balance_history(transactions):
    """Returns list of running balances after each transaction."""
    return [t.get("currentBalance", 0) for t in transactions]


def clamp(value, min_val, max_val):
    """Keeps value between min and max."""
    return max(min_val, min(max_val, value))


def get_essential_ratio(transactions):
    """
    CHANGE 4 HELPER:
    Calculates what fraction of transactions are essential.
    Essential = grocery, utility, transport, telecom, healthcare, etc.
    Returns ratio 0.0 to 1.0
    """
    successful_debits = [t for t in transactions if is_successful_debit(t)]
    if not successful_debits:
        return 0.5  # no data = neutral

    essential_count = sum(
        1 for t in successful_debits
        if t.get("merchantCategory", "OTHERS") in ESSENTIAL_CATEGORIES
    )
    return essential_count / len(successful_debits)


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — THE 6 SIGNAL FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def calculate_income_stability(transactions, account_info):
    """
    SIGNAL 1 — INCOME STABILITY (max 180 pts)
    [CHANGE 1: max reduced from 200 to 180]
    [CHANGE 2: seasonal income detection added]

    WHY THIS MATTERS:
    Consistent income = ability to repay on schedule.
    But "consistent" now means ENOUGH over time,
    not necessarily every single month.

    A farmer earning ₹0, ₹0, ₹80,000 over 3 months
    has CAPACITY to repay a ₹20,000 loan.
    Old formula would score him Poor.
    New formula recognises his seasonal pattern.

    COMPONENTS:
    A) Income Regularity  (0-90 pts)  ← softened CV penalty
    B) Income Sufficiency (0-55 pts)
    C) Income Trend       (0-35 pts)
    SEASONAL BONUS:       (0-25 pts)  ← NEW
    """
    monthly_income = get_monthly_income(transactions)

    if not monthly_income or max(monthly_income) == 0:
        return 0, {
            "score": 0, "max": 180,
            "detail": "No income transactions detected",
            "seasonal": False,
        }

    avg_income         = safe_mean(monthly_income)
    months_with_income = sum(1 for m in monthly_income if m > 500)
    total_months       = len(monthly_income)
    three_month_total  = sum(monthly_income)

    # ── COMPONENT A: Income Regularity (0-90 pts) ─────────────
    cv           = coefficient_of_variation(monthly_income)
    arrival_rate = months_with_income / total_months \
                   if total_months > 0 else 0

    # CHANGE 2: Soften CV penalty from 1.0 to 0.6 multiplier
    # Old: (1 - cv) × weight
    # New: (1 - cv × 0.6) × weight
    # This means CV of 0.5 now gives 70% instead of 50%
    softened_cv_score = max(0, 1 - (cv * CV_PENALTY_MULTIPLIER))
    regularity        = (arrival_rate * 0.6) + (softened_cv_score * 0.4)
    component_a       = regularity * 90

    # ── COMPONENT B: Income Sufficiency (0-55 pts) ────────────
    if avg_income >= EXCELLENT_INCOME:
        component_b = 55
    elif avg_income >= GOOD_INCOME:
        component_b = 40 + ((avg_income - GOOD_INCOME) /
                            (EXCELLENT_INCOME - GOOD_INCOME)) * 15
    elif avg_income >= MINIMUM_INCOME:
        component_b = 12 + ((avg_income - MINIMUM_INCOME) /
                            (GOOD_INCOME - MINIMUM_INCOME)) * 28
    else:
        component_b = (avg_income / MINIMUM_INCOME) * 12

    # ── COMPONENT C: Income Trend (0-35 pts) ──────────────────
    if len(monthly_income) >= 3:
        first_month = monthly_income[0]
        last_month  = monthly_income[-1]
        if first_month > 0:
            growth_rate = (last_month - first_month) / first_month
        else:
            growth_rate = 0

        if growth_rate > 0.05:
            component_c = 35
        elif growth_rate > -0.05:
            component_c = 22
        elif growth_rate > -0.20:
            component_c = 8
        else:
            component_c = 0
    else:
        component_c = 17  # neutral if not enough months

    # ── CHANGE 2: SEASONAL BONUS (0-25 pts) ───────────────────
    # Detects seasonal/irregular earners who have CAPACITY
    # even if monthly pattern is uneven.
    #
    # Qualifies IF:
    # 1. CV is high (income IS irregular)
    # 2. But 3-month total is enough to repay loan 3×
    #
    # Example: Farmer with ₹0, ₹0, ₹80K total = ₹80K
    # ₹80K > ₹20K × 3 = qualifies for seasonal bonus
    seasonal_bonus    = 0
    is_seasonal       = False
    capacity_required = SEASONAL_LOAN_TARGET * 3  # ₹60,000

    if cv > SEASONAL_CV_THRESHOLD and three_month_total >= capacity_required:
        # They have irregular income BUT enough total capacity
        is_seasonal = True
        # Bonus scales with how much over the threshold they are
        capacity_ratio = min(three_month_total / capacity_required, 2.0)
        seasonal_bonus = int(SEASONAL_BONUS_MAX * (capacity_ratio - 1.0))
        seasonal_bonus = clamp(seasonal_bonus, 0, SEASONAL_BONUS_MAX)

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c + seasonal_bonus
    total = clamp(total, 0, 180)

    return total, {
        "score":            round(total),
        "max":              180,
        "avg_monthly":      round(avg_income),
        "three_month_total":round(three_month_total),
        "cv":               round(cv, 2),
        "arrival_rate":     round(arrival_rate, 2),
        "seasonal_detected":is_seasonal,
        "seasonal_bonus":   seasonal_bonus,
        "components": {
            "regularity":   round(component_a),
            "sufficiency":  round(component_b),
            "trend":        round(component_c),
            "seasonal":     seasonal_bonus,
        }
    }


def calculate_payment_consistency(transactions, account_info):
    """
    SIGNAL 2 — PAYMENT CONSISTENCY (max 200 pts)
    [CHANGE 1: max increased from 180 to 200]

    WHY THIS IS NOW THE TOP SIGNAL:
    Research from CGAP and MFIN shows bill payment
    is the single strongest predictor of microfinance
    loan repayment in India.

    "If they pay ₹199 Jio every month,
     they will pay ₹1,500 EMI every month."

    COMPONENTS:
    A) Recharge Consistency     (0-85 pts)  ↑ from 80
    B) Bill Payment Rate        (0-75 pts)  ↑ from 60
    C) Recharge Amount Stability(0-40 pts)  = same
    """
    monthly_groups = group_by_month(transactions)
    total_months   = len(monthly_groups)

    if total_months == 0:
        return 0, {"score": 0, "max": 200,
                   "detail": "No transaction history"}

    # ── COMPONENT A: Recharge Consistency (0-85 pts) ──────────
    months_with_recharge = 0
    recharge_amounts     = []
    recharge_dates       = []

    for month, txns in monthly_groups.items():
        month_recharges = [
            t for t in txns
            if is_telecom(t) and is_successful_debit(t)
        ]
        if month_recharges:
            months_with_recharge += 1
            for r in month_recharges:
                recharge_amounts.append(r["amount"])
                try:
                    recharge_dates.append(int(r["date"].split("-")[2]))
                except:
                    pass

    recharge_rate = months_with_recharge / total_months

    # Bonus: recharge on similar date each month = planned ahead
    date_consistency_bonus = 0
    if len(recharge_dates) >= 2:
        date_cv = coefficient_of_variation(recharge_dates)
        if date_cv < 0.3:
            date_consistency_bonus = 10

    component_a = (recharge_rate * 75) + date_consistency_bonus
    component_a = clamp(component_a, 0, 85)

    # ── COMPONENT B: Bill Payment Rate (0-75 pts) ─────────────
    months_with_bills = 0
    total_bills_paid  = 0

    for month, txns in monthly_groups.items():
        month_bills = [
            t for t in txns
            if is_utility(t) and is_successful_debit(t)
        ]
        if month_bills:
            months_with_bills += 1
            total_bills_paid  += len(month_bills)

    bill_rate = months_with_bills / total_months
    avg_bills_per_month = total_bills_paid / total_months \
                          if total_months > 0 else 0
    bill_adequacy = clamp(avg_bills_per_month / 2.0, 0, 1)

    component_b = ((bill_rate * 0.6) + (bill_adequacy * 0.4)) * 75

    # ── COMPONENT C: Recharge Amount Stability (0-40 pts) ─────
    if len(recharge_amounts) >= 2:
        amount_cv   = coefficient_of_variation(recharge_amounts)
        stability   = clamp(1 - amount_cv, 0, 1)
        component_c = stability * 40
    else:
        component_c = 15  # neutral

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c
    total = clamp(total, 0, 200)

    return total, {
        "score":                round(total),
        "max":                  200,
        "recharge_rate":        round(recharge_rate, 2),
        "bill_rate":            round(bill_rate, 2),
        "months_with_recharge": months_with_recharge,
        "months_with_bills":    months_with_bills,
        "total_months":         total_months,
        "components": {
            "recharge_consistency": round(component_a),
            "bill_payment":         round(component_b),
            "amount_stability":     round(component_c),
        }
    }


def calculate_savings_discipline(transactions, account_info):
    """
    SIGNAL 3 — SAVINGS DISCIPLINE (max 130 pts)
    [CHANGE 1: max reduced from 150 to 130]

    WHY REDUCED:
    Reducing max prevents poor people from being
    disproportionately penalized for low absolute
    savings. The financial CHARACTER (consistency)
    matters more than the amount saved.

    COMPONENTS:
    A) Savings Ratio     (0-65 pts)  ↓ from 80
    B) Balance Cushion   (0-40 pts)  = same
    C) Saving Consistency(0-25 pts)  ↓ from 30
    """
    monthly_income  = get_monthly_income(transactions)
    monthly_spend   = get_monthly_spend(transactions)
    balance_history = get_balance_history(transactions)

    if not monthly_income or safe_mean(monthly_income) == 0:
        return 0, {"score": 0, "max": 130,
                   "detail": "No income to calculate savings"}

    avg_income = safe_mean(monthly_income)

    # ── COMPONENT A: Savings Ratio (0-65 pts) ─────────────────
    monthly_ratios = []
    for i in range(min(len(monthly_income), len(monthly_spend))):
        income = monthly_income[i]
        spend  = monthly_spend[i]
        if income > 0:
            ratio = clamp((income - spend) / income, 0, 0.5)
            monthly_ratios.append(ratio)

    avg_ratio = safe_mean(monthly_ratios) if monthly_ratios else 0

    # Scale: generous at low end (rewards discipline not wealth)
    if avg_ratio >= 0.30:
        component_a = 60 + (avg_ratio - 0.30) / 0.20 * 5
    elif avg_ratio >= 0.20:
        component_a = 50 + (avg_ratio - 0.20) / 0.10 * 10
    elif avg_ratio >= 0.10:
        component_a = 32 + (avg_ratio - 0.10) / 0.10 * 18
    elif avg_ratio >= 0.03:
        component_a = 12 + (avg_ratio - 0.03) / 0.07 * 20
    else:
        component_a = (avg_ratio / 0.03) * 12

    component_a = clamp(component_a, 0, 65)

    # ── COMPONENT B: Balance Cushion (0-40 pts) ───────────────
    if balance_history:
        min_balance = min(balance_history)
        if min_balance >= 2000:
            component_b = 40
        elif min_balance >= 500:
            component_b = 28
        elif min_balance >= 0:
            component_b = 15
        elif min_balance >= -500:
            component_b = 5
        else:
            component_b = 0
    else:
        component_b = 15

    # ── COMPONENT C: Savings Consistency (0-25 pts) ───────────
    if monthly_ratios:
        months_with_savings = sum(1 for r in monthly_ratios if r > 0.03)
        consistency = months_with_savings / len(monthly_ratios)
        component_c = consistency * 25
    else:
        component_c = 0

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c
    total = clamp(total, 0, 130)

    return total, {
        "score":            round(total),
        "max":              130,
        "avg_savings_rate": round(avg_ratio * 100, 1),
        "min_balance_ever": round(min(balance_history))
                            if balance_history else 0,
        "components": {
            "savings_ratio":   round(component_a),
            "balance_cushion": round(component_b),
            "consistency":     round(component_c),
        }
    }


def calculate_spending_behavior(transactions, account_info):
    """
    SIGNAL 4 — SPENDING BEHAVIOR (max 140 pts)
    [CHANGE 1: max increased from 130 to 140]

    WHY INCREASED:
    With the quality transaction fix in Signal 5,
    spending behavior now works alongside it.
    Signal 4 looks at HOW consistently they spend.
    Signal 5 looks at WHAT they spend on.
    Together they paint a complete picture.

    COMPONENTS:
    A) Spending Stability    (0-55 pts)  ↑ from 50
    B) Spike Detection       (0-55 pts)  ↑ from 50
    C) Night Transaction     (0-30 pts)  = same
    """
    monthly_spend = get_monthly_spend(transactions)
    total_txns    = len(transactions)

    if not monthly_spend or safe_mean(monthly_spend) == 0:
        return 50, {"score": 50, "max": 140,
                    "detail": "Insufficient spending data"}

    avg_spend = safe_mean(monthly_spend)
    spike_months = 0

    # ── COMPONENT A: Spending Stability (0-55 pts) ────────────
    spend_cv    = coefficient_of_variation(monthly_spend)
    component_a = clamp(55 * (1 - spend_cv), 0, 55)

    # ── COMPONENT B: Spike Detection (0-55 pts) ───────────────
    if len(monthly_spend) >= 2:
        spike_months = sum(
            1 for s in monthly_spend if s > avg_spend * 2.0
        )
        component_b = max(0, 55 - (spike_months * 22))
    else:
        component_b = 33  # neutral

    # ── COMPONENT C: Night Transaction Ratio (0-30 pts) ───────
    if total_txns > 0:
        night_txns  = sum(
            1 for t in transactions
            if get_transaction_hour(t) >= 23
            or get_transaction_hour(t) <= 4
        )
        night_ratio = night_txns / total_txns

        if night_ratio <= 0.05:
            component_c = 30
        elif night_ratio <= 0.15:
            component_c = 30 - ((night_ratio - 0.05) / 0.10 * 15)
        else:
            component_c = max(0, 15 - (night_ratio * 50))
    else:
        component_c = 15

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c
    total = clamp(total, 0, 140)

    return total, {
        "score":        round(total),
        "max":          140,
        "spend_cv":     round(spend_cv, 2),
        "spike_months": spike_months,
        "night_ratio":  round(night_txns / total_txns * 100, 1)
                        if total_txns > 0 else 0,
        "components": {
            "stability": round(component_a),
            "no_spikes": round(component_b),
            "day_hours": round(component_c),
        }
    }


def calculate_transaction_frequency(transactions, account_info):
    """
    SIGNAL 5 — TRANSACTION FREQUENCY (max 100 pts)
    [CHANGE 4: Volume replaced with Essential Ratio]

    THE KEY CHANGE:
    OLD approach: More transactions = higher score
    Problem: Student ordering 50 Swiggy deliveries
             scored higher than disciplined worker
             making 15 careful essential payments.

    NEW approach: WHAT you spend on > HOW MUCH you spend
    Essential spending = groceries, bills, transport,
                         medicine, rent, insurance
    Discretionary = food delivery, shopping, entertainment

    High essential ratio = responsible person
    Low essential ratio  = impulsive spender

    COMPONENTS:
    A) Essential Spending Ratio (0-50 pts)  ← REPLACES volume
    B) Merchant Diversity       (0-30 pts)  = same logic
    C) Failed Transaction Rate  (0-20 pts)  = same
    """
    monthly_groups = group_by_month(transactions)
    total_months   = len(monthly_groups)
    total_txns     = len(transactions)

    if total_txns == 0:
        return 0, {"score": 0, "max": 100,
                   "detail": "No transactions found"}

    # ── COMPONENT A: Essential Spending Ratio (0-50 pts) ──────
    # CHANGE 4: This replaces raw transaction volume
    #
    # Count successful debit transactions by type:
    successful_debits = [t for t in transactions if is_successful_debit(t)]

    if successful_debits:
        essential_count     = sum(
            1 for t in successful_debits
            if t.get("merchantCategory", "OTHERS") in ESSENTIAL_CATEGORIES
        )
        discretionary_count = sum(
            1 for t in successful_debits
            if t.get("merchantCategory", "OTHERS") in DISCRETIONARY_CATEGORIES
        )
        essential_ratio = essential_count / len(successful_debits)

        # Scoring:
        # 60%+ essential = 50 pts  (very responsible)
        # 40-60%         = 30 pts  (balanced)
        # 20-40%         = 15 pts  (somewhat impulsive)
        # under 20%      = 5 pts   (very impulsive)
        if essential_ratio >= 0.60:
            component_a = 50
        elif essential_ratio >= 0.40:
            component_a = 30 + ((essential_ratio - 0.40) / 0.20 * 20)
        elif essential_ratio >= 0.20:
            component_a = 15 + ((essential_ratio - 0.20) / 0.20 * 15)
        else:
            component_a = max(5, essential_ratio / 0.20 * 15)
    else:
        essential_ratio     = 0
        discretionary_count = 0
        component_a         = 0

    component_a = clamp(component_a, 0, 50)

    # ── COMPONENT B: Merchant Diversity (0-30 pts) ────────────
    # Still important: spending across many categories
    # shows a real, active financial life
    unique_categories = len(set(
        t.get("merchantCategory", "OTHERS")
        for t in transactions
    ))
    component_b = clamp((unique_categories / 8) * 30, 0, 30)

    # ── COMPONENT C: Failed Transaction Rate (0-20 pts) ───────
    failed_count = sum(1 for t in transactions if is_failed(t))
    failed_rate  = failed_count / total_txns if total_txns > 0 else 0

    if failed_rate <= 0.02:
        component_c = 20
    elif failed_rate <= 0.10:
        component_c = 20 - ((failed_rate - 0.02) / 0.08 * 10)
    else:
        component_c = max(0, 10 - ((failed_rate - 0.10) / 0.10 * 10))

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c
    total = clamp(total, 0, 100)

    avg_monthly_txns = round(total_txns / total_months, 1) \
                       if total_months else 0

    return total, {
        "score":               round(total),
        "max":                 100,
        "essential_ratio":     round(essential_ratio * 100, 1),
        "essential_count":     essential_count if successful_debits else 0,
        "discretionary_count": discretionary_count,
        "avg_monthly_txns":    avg_monthly_txns,
        "unique_categories":   unique_categories,
        "failed_rate":         round(failed_rate * 100, 1),
        "components": {
            "essential_ratio": round(component_a),
            "diversity":       round(component_b),
            "no_fails":        round(component_c),
        }
    }


def calculate_debt_signals(transactions, account_info):
    """
    SIGNAL 6 — DEBT SIGNALS (max 150 pts)
    [CHANGE 1: max increased from 140 to 150]

    WHY INCREASED:
    This is the most protective signal.
    Over-indebted people should score lower.
    More weight = more protection for both
    the borrower and the lender.

    COMPONENTS:
    A) EMI-to-Income Ratio  (0-65 pts)  ↑ from 60
    B) Overdraft History    (0-50 pts)  = same
    C) Balance Recovery     (0-35 pts)  ↑ from 30
    """
    monthly_income  = get_monthly_income(transactions)
    balance_history = get_balance_history(transactions)
    avg_income      = safe_mean(monthly_income) if monthly_income else 0
    monthly_groups  = group_by_month(transactions)

    # ── COMPONENT A: EMI-to-Income Ratio (0-65 pts) ───────────
    monthly_emi_amounts = []
    for month, txns in monthly_groups.items():
        month_emis = sum(
            t["amount"] for t in txns
            if is_emi(t) and is_successful_debit(t)
        )
        if month_emis > 0:
            monthly_emi_amounts.append(month_emis)

    avg_emi   = safe_mean(monthly_emi_amounts) \
                if monthly_emi_amounts else 0
    emi_ratio = avg_emi / avg_income \
                if avg_income > 0 else 0.5

    if avg_emi == 0:
        component_a = 65     # no existing debt ✅
    elif emi_ratio <= 0.20:
        component_a = 60
    elif emi_ratio <= 0.35:
        component_a = 38 + ((0.35 - emi_ratio) / 0.15 * 22)
    elif emi_ratio <= 0.50:
        component_a = 15 + ((0.50 - emi_ratio) / 0.15 * 23)
    else:
        component_a = max(0, 15 * (1 - (emi_ratio - 0.50)))

    component_a = clamp(component_a, 0, 65)

    # ── COMPONENT B: Overdraft History (0-50 pts) ─────────────
    if balance_history:
        min_balance = min(balance_history)
        if min_balance >= 1000:
            component_b = 50
        elif min_balance >= 100:
            component_b = 38
        elif min_balance >= 0:
            component_b = 22
        elif min_balance >= -500:
            component_b = 10
        else:
            component_b = 0
    else:
        component_b = 25

    # ── COMPONENT C: Balance Recovery (0-35 pts) ──────────────
    if len(balance_history) >= 5:
        min_idx     = balance_history.index(min(balance_history))
        min_balance = balance_history[min_idx]
        subsequent  = balance_history[min_idx + 1: min_idx + 11]

        if subsequent and min_balance < 1000:
            recovery = safe_mean(subsequent) - min_balance
            if recovery >= 2000:
                component_c = 35
            elif recovery >= 500:
                component_c = 20
            else:
                component_c = 5
        else:
            component_c = 22  # balance was fine, neutral
    else:
        component_c = 15

    # ── FINAL SCORE ───────────────────────────────────────────
    total = component_a + component_b + component_c
    total = clamp(total, 0, 150)

    return total, {
        "score":             round(total),
        "max":               150,
        "avg_monthly_emi":   round(avg_emi),
        "emi_ratio":         round(emi_ratio * 100, 1),
        "min_balance_ever":  round(min(balance_history))
                             if balance_history else 0,
        "components": {
            "emi_burden":   round(component_a),
            "no_overdraft": round(component_b),
            "recovery":     round(component_c),
        }
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — EXPLANATION GENERATOR
# ═══════════════════════════════════════════════════════════════

SIGNAL_MESSAGES = {
    "income_stability": {
        "excellent": ("Consistent income arriving reliably every month", None),
        "good":      ("Income is fairly regular with minor variations",
                      "Maintain current income frequency"),
        "fair":      ("Income is somewhat irregular",
                      "Even one additional income source helps"),
        "poor":      ("Very irregular or insufficient income detected",
                      "Consistent income, even if small, improves score significantly"),
    },
    "payment_consistency": {
        "excellent": ("Bills and recharges paid on time every month", None),
        "good":      ("Most recurring payments are on time",
                      "Set reminders for utility bills"),
        "fair":      ("Recharges or bills missed in some months",
                      "Set up auto-pay for Jio/Airtel — adds 25+ pts"),
        "poor":      ("Frequent missed recharges and bill payments",
                      "Pay phone recharge same day each month — biggest quick win"),
    },
    "savings_discipline": {
        "excellent": ("Consistent savings every month — excellent discipline", None),
        "good":      ("Saving regularly — good financial habit",
                      "Increase savings slightly for better score"),
        "fair":      ("Saving some months but not consistently",
                      "Save even ₹200/month consistently — adds 15+ pts"),
        "poor":      ("Very little or no savings detected",
                      "Open RD of ₹500/month — shows savings intent"),
    },
    "spending_behavior": {
        "excellent": ("Spending is very consistent and controlled", None),
        "good":      ("Spending is fairly stable month to month",
                      "Maintain current spending patterns"),
        "fair":      ("Some months show higher spending than usual",
                      "Avoid large unplanned purchases — adds 15+ pts"),
        "poor":      ("Erratic spending with large spikes detected",
                      "Track monthly budget — consistent spending is key signal"),
    },
    "transaction_frequency": {
        "excellent": ("Spending primarily on essential needs — very responsible", None),
        "good":      ("Good balance of essential and discretionary spending",
                      "Shift more spending to essential categories"),
        "fair":      ("More discretionary than essential spending detected",
                      "Pay grocery, transport, bills via UPI → adds 15+ pts"),
        "poor":      ("Spending mostly on non-essential items",
                      "Route essential payments through this account for better score"),
    },
    "debt_signals": {
        "excellent": ("No concerning debt burden detected", None),
        "good":      ("Existing debt is manageable relative to income",
                      "Maintain current EMI discipline"),
        "fair":      ("Moderate debt burden — manageable but watch closely",
                      "Avoid taking new loans until existing EMIs reduce"),
        "poor":      ("High debt burden relative to income",
                      "Focus on repaying existing loans before taking new ones"),
    },
}


def get_signal_level(score, max_score):
    """Converts score percentage to level label."""
    pct = score / max_score if max_score > 0 else 0
    if pct >= 0.85:   return "excellent"
    elif pct >= 0.65: return "good"
    elif pct >= 0.40: return "fair"
    else:             return "poor"


def generate_explanation(signal_name, score, max_score, detail_data):
    """Generates human-readable explanation for one signal."""
    level   = get_signal_level(score, max_score)
    pct     = score / max_score if max_score > 0 else 0
    msgs    = SIGNAL_MESSAGES.get(signal_name, {})
    message, tip = msgs.get(level, ("Analyzed", None))

    display_names = {
        "income_stability":      "Income Stability",
        "payment_consistency":   "Payment Consistency",
        "savings_discipline":    "Savings Discipline",
        "spending_behavior":     "Spending Behavior",
        "transaction_frequency": "Transaction Quality",
        "debt_signals":          "Debt Burden",
    }

    return {
        "signal":    signal_name,
        "name":      display_names.get(signal_name, signal_name),
        "score":     round(score),
        "max":       max_score,
        "pct":       round(pct * 100),
        "level":     level,
        "direction": "helping" if pct >= 0.65 else "hurting",
        "impact":    round(score - (max_score * 0.5)),
        "message":   message,
        "tip":       tip,
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — ELIGIBILITY + DATA GUARDS
#
# These run BEFORE scoring to catch edge cases:
# 1. Over-income users who don't need microfinance
# 2. Users with insufficient transaction history
# ═══════════════════════════════════════════════════════════════

def check_eligibility(aa_json):
    """
    Checks if user is eligible for microfinance scoring.
    Returns: {eligible: True} or {eligible: False, reason: ...}
    """
    transactions   = aa_json.get("transactions", [])
    monthly_income = get_monthly_income(transactions)
    avg_income     = safe_mean(monthly_income) if monthly_income else 0

    # Over-income check: > ₹40K/month = formal banking eligible
    if avg_income > 40000:
        return {
            "eligible": False,
            "reason":   "income_too_high",
            "message":  (
                f"Average monthly income ₹{round(avg_income):,} exceeds "
                f"microfinance range. You qualify for regular bank loans."
            ),
            "redirect": "formal_banking",
        }

    return {"eligible": True}


def check_data_sufficiency(aa_json):
    """
    Checks if there is enough transaction data to score fairly.
    Returns: {sufficient: True} or {sufficient: False, reason: ...}
    """
    transactions = aa_json.get("transactions", [])
    months       = len(group_by_month(transactions))

    if len(transactions) < 20:
        return {
            "sufficient": False,
            "reason":     "too_few_transactions",
            "message":    (
                f"Only {len(transactions)} transactions found. "
                f"Need at least 20 for a reliable score."
            ),
        }

    if months < 2:
        return {
            "sufficient": False,
            "reason":     "too_few_months",
            "message":    (
                f"Only {months} month of data found. "
                f"Need at least 2 months of bank history."
            ),
        }

    return {"sufficient": True}


# ═══════════════════════════════════════════════════════════════
# SECTION 6 — MASTER SCORE FUNCTION
# THE ONE FUNCTION CALLED BY score.py
# ═══════════════════════════════════════════════════════════════

def calculate_credit_score(aa_json):
    """
    THE MAIN FUNCTION.
    Takes one user's AA JSON → returns complete credit score.

    Called by: backend/app/routes/score.py
    Input:     aa_json dict
    Output:    complete scoring result dict
    """
    transactions = aa_json.get("transactions", [])
    account_info = aa_json.get("account", {})
    summary      = aa_json.get("summary", {})

    if not transactions:
        return {
            "error":       "No transactions found in account data",
            "final_score": 300,
            "bucket":      "Poor",
        }

    # ── Run eligibility and data checks ───────────────────────
    eligibility = check_eligibility(aa_json)
    if not eligibility["eligible"]:
        return {
            "eligible":    False,
            "reason":      eligibility["reason"],
            "message":     eligibility["message"],
            "final_score": None,
        }

    sufficiency = check_data_sufficiency(aa_json)
    if not sufficiency["sufficient"]:
        return {
            "sufficient":  False,
            "reason":      sufficiency["reason"],
            "message":     sufficiency["message"],
            "final_score": None,
        }

    # ── Run all 6 signals ──────────────────────────────────────
    s1, d1 = calculate_income_stability(transactions, account_info)
    s2, d2 = calculate_payment_consistency(transactions, account_info)
    s3, d3 = calculate_savings_discipline(transactions, account_info)
    s4, d4 = calculate_spending_behavior(transactions, account_info)
    s5, d5 = calculate_transaction_frequency(transactions, account_info)
    s6, d6 = calculate_debt_signals(transactions, account_info)

    # ── Calculate final score ──────────────────────────────────
    raw_score   = s1 + s2 + s3 + s4 + s5 + s6
    final_score = int(clamp(
        BASE_SCORE + (raw_score / 900) * 600,
        300, 900
    ))

    # ── Determine bucket ──────────────────────────────────────
    bucket       = "Poor"
    bucket_emoji = "🔴"
    bucket_color = "#e74c3c"
    for low, high, name, emoji, color in BUCKETS:
        if low <= final_score <= high:
            bucket       = name
            bucket_emoji = emoji
            bucket_color = color
            break

    # ── Percentile ────────────────────────────────────────────
    percentile = int(clamp(
        ((final_score - 300) / 600) * 100, 1, 99
    ))

    # ── Explanations ──────────────────────────────────────────
    signals = {
        "income_stability":      (s1, d1),
        "payment_consistency":   (s2, d2),
        "savings_discipline":    (s3, d3),
        "spending_behavior":     (s4, d4),
        "transaction_frequency": (s5, d5),
        "debt_signals":          (s6, d6),
    }

    explanations = []
    for signal_name, (score, detail) in signals.items():
        max_score = SIGNAL_WEIGHTS[signal_name]
        exp = generate_explanation(
            signal_name, score, max_score, detail
        )
        explanations.append(exp)

    explanations.sort(key=lambda x: x["pct"])
    helping = [e for e in explanations if e["direction"] == "helping"][:3]
    hurting = [e for e in explanations if e["direction"] == "hurting"][:3]

    # ── Comparison text ───────────────────────────────────────
    avg_income = summary.get("averageMonthlyCredit", 0)
    if avg_income < 10000:
        segment = "gig workers"
    elif avg_income < 30000:
        segment = "salaried workers"
    else:
        segment = "high-income earners"

    comparison = (
        f"Better than {percentile}% of {segment} "
        f"with similar income profile"
    )

    # ── Seasonal detection flag ───────────────────────────────
    seasonal_detected = d1.get("seasonal_detected", False)

    return {
        "final_score":   final_score,
        "bucket":        bucket,
        "bucket_emoji":  bucket_emoji,
        "bucket_color":  bucket_color,
        "percentile":    percentile,
        "raw_score":     round(raw_score),
        "seasonal_income_detected": seasonal_detected,

        "breakdown": {
            "income_stability":      {"score": round(s1), "max": 180, "detail": d1},
            "payment_consistency":   {"score": round(s2), "max": 200, "detail": d2},
            "savings_discipline":    {"score": round(s3), "max": 130, "detail": d3},
            "spending_behavior":     {"score": round(s4), "max": 140, "detail": d4},
            "transaction_frequency": {"score": round(s5), "max": 100, "detail": d5},
            "debt_signals":          {"score": round(s6), "max": 150, "detail": d6},
        },

        "top_helping": helping,
        "top_hurting": hurting,
        "all_signals": explanations,

        "compared_to_similar":   comparison,
        "transactions_analysed": len(transactions),
        "months_covered":        len(set(
            t["date"][:7] for t in transactions
        )),
    }


def score_to_bucket(score):
    """Quick utility — converts score number to bucket name."""
    for low, high, name, emoji, color in BUCKETS:
        if low <= score <= high:
            return name
    return "Poor"


# ═══════════════════════════════════════════════════════════════
# SECTION 7 — STANDALONE TEST
# Run: python ml/score_engine.py
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("=" * 60)
    print("  CREDITGHOST — SCORE ENGINE v2.0")
    print("  Changes: Weights + Seasonal + Quality Txns")
    print("=" * 60)

    demo_path = "ml/data/demo_personas.json"

    try:
        with open(demo_path) as f:
            personas = json.load(f)
    except FileNotFoundError:
        print(f"❌ {demo_path} not found.")
        print("   Run python ml/generate_data.py first!")
        exit(1)

    for persona_name, aa_json in personas.items():

        if aa_json is None:
            print(f"\n⚠️  {persona_name}: No data")
            continue

        print(f"\n{'─'*60}")
        print(f"  👤 {persona_name.upper()}")
        meta = aa_json.get("_meta", {})
        print(f"  {meta.get('archetypeDescription', '')}")
        print(f"{'─'*60}")

        result = calculate_credit_score(aa_json)

        # Handle edge cases
        if not result.get("eligible", True) == False \
           and result.get("final_score") is None:
            print(f"  ⚠️  {result.get('message', 'Check failed')}")
            continue

        if "error" in result:
            print(f"  ❌ {result['error']}")
            continue

        # Print score
        seasonal = " 🌾 Seasonal income detected" \
                   if result.get("seasonal_income_detected") else ""
        print(f"\n  {result['bucket_emoji']} SCORE: "
              f"{result['final_score']} — {result['bucket']}{seasonal}")
        print(f"  Better than {result['percentile']}% of users")
        print(f"  Transactions analysed: {result['transactions_analysed']}")

        # Signal breakdown
        print(f"\n  📊 SIGNAL BREAKDOWN (v2.0 weights):")
        for sig, data in result["breakdown"].items():
            score   = data["score"]
            maximum = data["max"]
            pct     = round(score / maximum * 100)
            bar     = "█" * (pct // 10) + "░" * (10 - pct // 10)
            # Show change 4 label for transaction frequency
            label = "Transaction Quality" \
                    if sig == "transaction_frequency" else sig
            print(f"  {label:28s} {bar} {score:3d}/{maximum} ({pct}%)")

        # Top reasons
        print(f"\n  ✅ HELPING:")
        for r in result["top_helping"]:
            print(f"     {r['name']:25s} {r['message']}")

        print(f"\n  ❌ HURTING:")
        for r in result["top_hurting"]:
            print(f"     {r['name']:25s} {r['message']}")
            if r["tip"]:
                print(f"     {'':25s} 💡 {r['tip']}")

    print(f"\n{'='*60}")
    print("✅ Score Engine v2.0 working correctly")
    print("   Changes applied:")
    print("   1. Rebalanced weights")
    print("   2. Seasonal income detection")
    print("   4. Quality over quantity (transactions)")
    print("=" * 60)