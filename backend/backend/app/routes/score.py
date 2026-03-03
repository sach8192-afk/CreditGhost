# ═══════════════════════════════════════════════════════════════
# CreditGhost — API Routes (score.py)
# ═══════════════════════════════════════════════════════════════
#
# WHAT THIS FILE DOES:
# This file is the bridge between your React frontend
# and your Python ML pipeline.
#
# Frontend sends a request → score.py receives it →
# calls score_engine + train + explain →
# sends everything back to frontend as JSON.
#
# ENDPOINTS IN THIS FILE:
#
#   GET  /health
#        → Is the server running? Are models loaded?
#        → Used to check everything is working
#
#   GET  /demo/{name}
#        → Returns pre-computed score for ramesh/priya/arjun
#        → Pre-loaded at startup for instant response (~12ms)
#        → Used during PITCH DEMO — never fails, never slow
#
#   POST /score
#        → Receives real AA JSON from frontend
#        → Runs full pipeline: score + trust + explain
#        → Returns complete result
#        → Used for real user flow
#
#   GET  /explain/{name}
#        → Returns pre-computed explanation for demo personas
#        → Powers "Why this score?" button on result page
# ═══════════════════════════════════════════════════════════════

import json
import os
import sys
import pickle
import time

# Add project root so Python finds ml/ folder
sys.path.append(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)

from fastapi          import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# ── Import ML pipeline ────────────────────────────────────────
# These are the 3 files we already built
from ml.score_engine import calculate_credit_score
from ml.train        import predict_trust
from ml.explain      import generate_explanation


# ── Create router ─────────────────────────────────────────────
# Router is a mini-app that holds related endpoints.
# main.py attaches this router to the main server.
router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# STARTUP — Load everything into memory ONCE
#
# WHY LOAD AT STARTUP?
# Loading a file from disk takes 200-500ms.
# If we load on every request: every demo is slow.
# If we load once at startup: every demo is instant.
#
# This is called "caching" — store in memory, read from memory.
# ═══════════════════════════════════════════════════════════════

# ── Load XGBoost trust model ──────────────────────────────────
TRUST_MODEL = None

try:
    model_path = "ml/models/anomaly_detector.pkl"
    with open(model_path, "rb") as f:
        TRUST_MODEL = pickle.load(f)
    print("✅ Trust model loaded")
except FileNotFoundError:
    print("⚠️  Trust model not found at ml/models/anomaly_detector.pkl")
    print("   Run: python ml/train.py")
except Exception as e:
    print(f"⚠️  Trust model load error: {e}")


# ── Load demo personas ────────────────────────────────────────
# These are Ramesh, Priya, Arjun from generate_data.py
DEMO_PERSONAS = {}

try:
    with open("ml/data/demo_personas.json") as f:
        DEMO_PERSONAS = json.load(f)
    print(f"✅ Demo personas loaded: {list(DEMO_PERSONAS.keys())}")
except FileNotFoundError:
    print("⚠️  demo_personas.json not found")
    print("   Run: python ml/generate_data.py")
except Exception as e:
    print(f"⚠️  Personas load error: {e}")


# ── Load pre-generated explanations ──────────────────────────
# These are from explain.py — pre-computed for speed
DEMO_EXPLANATIONS = {}

try:
    with open("ml/data/demo_explanations.json", encoding="utf-8") as f:
        DEMO_EXPLANATIONS = json.load(f)
    print(f"✅ Demo explanations loaded")
except FileNotFoundError:
    print("⚠️  demo_explanations.json not found")
    print("   Run: python ml/explain.py")
except Exception as e:
    print(f"⚠️  Explanations load error: {e}")


# ═══════════════════════════════════════════════════════════════
# NEW ENDPOINT — POST /analyze
#
# WHAT IT DOES:
# Accepts a user name from frontend.
# Maps it to a demo persona using dictionary lookup.
# Returns pre-computed demo result.
#
# This keeps frontend clean and moves persona logic to backend.
# ═══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    name: str


# Dictionary mapping for demo personas
PERSONA_MAP = {
    "ramesh": "ramesh",
    "priya":  "priya",
    "arjun":  "arjun",
}


@router.post("/analyze")
async def analyze_by_name(payload: AnalyzeRequest):
    """
    Example:
        POST /analyze
        {
            "name": "Priya Nair"
        }

    Returns:
        Pre-computed demo result for matched persona.
    """

    entered_name = payload.name.lower().strip()

    # Default fallback persona
    persona = "ramesh"

    # Dictionary-based mapping
    for key in PERSONA_MAP:
        if key in entered_name:
            persona = PERSONA_MAP[key]
            break

    # Return pre-computed result (fast, safe)
    if persona in DEMO_RESULTS:
        return DEMO_RESULTS[persona]

    raise HTTPException(
        status_code=404,
        detail=f"No demo result found for '{persona}'"
    )


# ── Pre-compute full demo results at startup ──────────────────
# Runs score + trust on Ramesh/Priya/Arjun once at startup.
# Every /demo/{name} call just returns from this dict.
# Response time: ~5ms instead of ~800ms.
DEMO_RESULTS = {}

if DEMO_PERSONAS and TRUST_MODEL:
    print("⚙️  Pre-computing demo results...")
    for name, aa_json in DEMO_PERSONAS.items():
        if aa_json is None:
            continue
        try:
            # Credit score from formula
            score_result = calculate_credit_score(aa_json)

            if score_result.get("final_score") is None:
                continue

            credit_score = score_result["final_score"]

            # Trust score from XGBoost
            trust_result = predict_trust(
                TRUST_MODEL, aa_json, credit_score
            )

            # Combine into one result
            DEMO_RESULTS[name] = {
                **score_result,
                "trust": trust_result,
                "persona": name,
            }
            print(f"  ✅ {name}: {credit_score} "
                  f"({score_result['bucket']}) | "
                  f"Trust {trust_result['trust_score']}/100 "
                  f"{trust_result['trust_level']['emoji']}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

    print(f"✅ Demo results ready for {list(DEMO_RESULTS.keys())}")
elif not TRUST_MODEL:
    print("⚠️  Skipping demo pre-compute — trust model not loaded")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 1 — GET /health
# Quick check that server + models are all working
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """
    Returns status of server and all loaded components.
    Call this first to verify everything is working.
    """
    return {
        "status":        "healthy ✅",
        "version":       "2.0.0",
        "models": {
            "trust_model":      TRUST_MODEL is not None,
            "demo_personas":    len(DEMO_PERSONAS),
            "demo_results":     len(DEMO_RESULTS),
            "demo_explanations":len(DEMO_EXPLANATIONS),
        },
        "ready_for_demo": len(DEMO_RESULTS) == 3,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 2 — GET /demo/{name}
#
# WHAT IT DOES:
# Returns complete pre-computed score for Ramesh/Priya/Arjun.
# This is your PITCH DEMO button.
#
# WHY PRE-COMPUTED?
# During pitch demo you cannot afford:
# - Slow response (judges lose interest)
# - Runtime error (game over)
# - No WiFi (server unreachable)
#
# Pre-computing means result is in memory.
# Response in 5ms. Never fails.
# ═══════════════════════════════════════════════════════════════

@router.get("/demo/{persona_name}")
async def get_demo_score(persona_name: str):
    """
    Returns pre-computed score for demo personas.

    Usage:
      GET /demo/ramesh
      GET /demo/priya
      GET /demo/arjun
    """
    name = persona_name.lower().strip()

    # Validate persona name
    valid_names = ["ramesh", "priya", "arjun"]
    if name not in valid_names:
        raise HTTPException(
            status_code = 404,
            detail      = f"Unknown persona '{name}'. Use: {valid_names}"
        )

    # Return pre-computed result
    if name in DEMO_RESULTS:
        return DEMO_RESULTS[name]

    # Fallback: compute on the fly if pre-compute failed
    if name not in DEMO_PERSONAS or DEMO_PERSONAS[name] is None:
        raise HTTPException(
            status_code = 404,
            detail      = f"No data for '{name}'. Run generate_data.py"
        )

    # Runtime compute (slower but works as fallback)
    aa_json      = DEMO_PERSONAS[name]
    score_result = calculate_credit_score(aa_json)

    if score_result.get("final_score") is None:
        raise HTTPException(
            status_code = 422,
            detail      = score_result.get("message", "Scoring failed")
        )

    credit_score = score_result["final_score"]

    trust_result = {}
    if TRUST_MODEL:
        trust_result = predict_trust(TRUST_MODEL, aa_json, credit_score)

    return {
        **score_result,
        "trust":   trust_result,
        "persona": name,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 3 — POST /score
#
# WHAT IT DOES:
# Receives a real user's AA JSON from the frontend.
# Runs the complete pipeline:
#   1. Check eligibility (income < ₹40K/month)
#   2. Check data sufficiency (≥ 20 transactions)
#   3. Calculate credit score (score_engine.py)
#   4. Calculate trust score (train.py XGBoost)
#   5. Generate explanation (explain.py)
#   6. Return everything as one JSON
#
# FRONTEND CALLS THIS AS:
#   fetch("http://localhost:8000/score", {
#     method: "POST",
#     headers: {"Content-Type": "application/json"},
#     body: JSON.stringify(aaJson)
#   })
# ═══════════════════════════════════════════════════════════════

@router.post("/score")
async def score_user(aa_json: dict):
    """
    Main scoring endpoint for real users.

    Input:  Complete AA JSON (Setu/AA framework format)
    Output: Credit score + Trust score + Explanation

    The frontend sends the AA JSON received from the
    Account Aggregator after user consent.
    """
    start_time = time.time()

    # ── Validate input ────────────────────────────────────────
    if not aa_json:
        raise HTTPException(
            status_code = 400,
            detail      = "Empty request body"
        )

    if "transactions" not in aa_json:
        raise HTTPException(
            status_code = 400,
            detail      = "Missing 'transactions' in AA JSON"
        )

    if len(aa_json["transactions"]) == 0:
        raise HTTPException(
            status_code = 422,
            detail      = "No transactions found in AA data"
        )

    # ── Step 1: Calculate credit score ───────────────────────
    try:
        score_result = calculate_credit_score(aa_json)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Score calculation failed: {str(e)}"
        )

    # ── Handle eligibility/sufficiency failures ───────────────
    # These are not errors — they are valid responses
    if score_result.get("eligible") == False:
        return JSONResponse(
            status_code = 200,
            content     = {
                "eligible": False,
                "message":  score_result.get("message"),
                "reason":   score_result.get("reason"),
            }
        )

    if score_result.get("sufficient") == False:
        return JSONResponse(
            status_code = 200,
            content     = {
                "sufficient": False,
                "message":    score_result.get("message"),
                "reason":     score_result.get("reason"),
            }
        )

    if score_result.get("final_score") is None:
        raise HTTPException(
            status_code = 422,
            detail      = "Could not calculate score"
        )

    credit_score = score_result["final_score"]

    # ── Step 2: Calculate trust score ────────────────────────
    trust_result = {}
    if TRUST_MODEL:
        try:
            trust_result = predict_trust(
                TRUST_MODEL, aa_json, credit_score
            )
        except Exception as e:
            # Trust score failure should NOT block credit score
            trust_result = {
                "trust_score":  50,
                "trust_level":  {
                    "label":       "Normal",
                    "emoji":       "🟡",
                    "color":       "#d97706",
                    "description": "Trust model unavailable",
                },
                "adjusted_credit_score": credit_score,
                "score_change":          0,
                "error":                 str(e),
            }
    else:
        trust_result = {
            "trust_score": 50,
            "trust_level": {
                "label":       "Normal",
                "emoji":       "🟡",
                "color":       "#d97706",
                "description": "Trust model not loaded",
            },
            "adjusted_credit_score": credit_score,
            "score_change":          0,
        }

    # ── Step 3: Generate explanation ──────────────────────────
    try:
        explanation = generate_explanation(aa_json)
    except Exception as e:
        # Explanation failure should NOT block scoring
        explanation = {"error": str(e)}

    # ── Step 4: Build final response ──────────────────────────
    processing_ms = round((time.time() - start_time) * 1000)

    return {
        # ── Core scores ───────────────────────────────────────
        "final_score":   credit_score,
        "bucket":        score_result["bucket"],
        "bucket_emoji":  score_result["bucket_emoji"],
        "bucket_color":  score_result["bucket_color"],
        "percentile":    score_result["percentile"],

        # ── Trust layer ───────────────────────────────────────
        "trust":         trust_result,

        # ── Signal breakdown (for bar chart) ─────────────────
        "breakdown":     score_result["breakdown"],

        # ── Explanation cards (for "Why?" button) ─────────────
        "explanation":   explanation,

        # ── Summary cards ─────────────────────────────────────
        "top_helping":   score_result.get("top_helping", []),
        "top_hurting":   score_result.get("top_hurting", []),

        # ── Metadata ──────────────────────────────────────────
        "transactions_analysed":       score_result["transactions_analysed"],
        "months_covered":              score_result["months_covered"],
        "seasonal_income_detected":    score_result.get(
                                           "seasonal_income_detected", False
                                       ),
        "compared_to_similar":         score_result.get("compared_to_similar", ""),
        "processing_ms":               processing_ms,
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT 4 — GET /explain/{name}
#
# WHAT IT DOES:
# Returns pre-computed explanation for demo personas.
# Powers the "Why this score?" button on result page.
#
# WHY SEPARATE FROM /demo?
# /demo returns the score.
# /explain returns WHY — detailed signal breakdowns
# with real evidence from transactions.
#
# Keeping them separate means:
# - Score page loads fast (no explanation computation)
# - Explanation only loads when user clicks the button
# ═══════════════════════════════════════════════════════════════

@router.get("/explain/{persona_name}")
async def get_explanation(persona_name: str):
    """
    Returns pre-computed explanation for demo personas.

    Usage:
      GET /explain/ramesh
      GET /explain/priya
      GET /explain/arjun

    Called when user clicks "Why this score?" button.
    """
    name = persona_name.lower().strip()

    valid_names = ["ramesh", "priya", "arjun"]
    if name not in valid_names:
        raise HTTPException(
            status_code = 404,
            detail      = f"Unknown persona '{name}'. Use: {valid_names}"
        )

    # Return pre-generated explanation
    if name in DEMO_EXPLANATIONS and DEMO_EXPLANATIONS[name]:
        return DEMO_EXPLANATIONS[name]

    # Fallback: generate on the fly
    if name not in DEMO_PERSONAS or DEMO_PERSONAS[name] is None:
        raise HTTPException(
            status_code = 404,
            detail      = f"No data for '{name}'"
        )

    try:
        explanation = generate_explanation(DEMO_PERSONAS[name])
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Explanation generation failed: {str(e)}"
        )