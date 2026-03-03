# ═══════════════════════════════════════════════════════════════
# CreditGhost — API Server (main.py)
# ═══════════════════════════════════════════════════════════════
#
# WHAT THIS FILE DOES:
# This is the entry point for the entire backend.
# Think of it as the "front door" of your restaurant.
# It starts the server and tells it which routes exist.
#
# HOW TO RUN:
#   cd C:\Users\rajan\TARUN\CreditGhost
#   uvicorn backend.app.main:app --reload --port 8000
#
# WHAT --reload MEANS:
#   Every time you save a file, server restarts automatically.
#   Use this during development. Remove in production.
#
# AFTER RUNNING, TEST THESE IN BROWSER:
#   http://localhost:8000/          → health check
#   http://localhost:8000/docs      → auto API documentation
#   http://localhost:8000/demo/ramesh → Ramesh's score
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes.score import router


# ── Create the FastAPI app ────────────────────────────────────
# FastAPI is a Python web framework.
# app = the actual server object everything attaches to.
app = FastAPI(
    title       = "CreditGhost API",
    description = "Alternative credit scoring for credit-invisible Indians",
    version     = "2.0.0",
)


# ── CORS Middleware ───────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
#
# WITHOUT THIS: Browser blocks React from calling this API.
# Browsers have a security rule:
#   "Frontend on localhost:3000 cannot call
#    backend on localhost:8000 unless backend allows it."
#
# allow_origins=["*"] means allow ALL origins.
# Fine for hackathon. In production use specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Attach all routes from score.py ──────────────────────────
# router contains all our endpoints (/score, /demo, /explain)
# including it here makes them available on the server.
app.include_router(router)


# ── Root endpoint ─────────────────────────────────────────────
# Simple health check. If this returns, server is running.
# Judges can verify the backend is live during demo.
@app.get("/")
async def root():
    return {
        "status":      "CreditGhost API running ✅",
        "version":     "2.0.0",
        "description": "Alternative credit scoring for credit-invisible Indians",
        "endpoints": {
            "health":       "GET /health",
            "demo":         "GET /demo/{ramesh|priya|arjun}",
            "score":        "POST /score",
            "explain":      "GET /explain/{ramesh|priya|arjun}",
            "docs":         "GET /docs",
        }
    }