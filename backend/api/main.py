"""
main.py
───────
FastAPI application entry point for CinePulse-Indic backend.

Serves aggregated JSON data and handles comment filtering
from CSV files — no database required.

Run:
  cd backend
  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analysis, comments, report

app = FastAPI(
    title       = "CinePulse-Indic API",
    description = "Cross-Linguistic Sentiment Analysis for Pan-Indian Cinema",
    version     = "1.0.0",
)

# ── CORS — allow React dev server ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(comments.router, prefix="/api", tags=["Comments"])
app.include_router(report.router,   prefix="/api", tags=["Report"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "CinePulse-Indic API",
        "status" : "running",
        "docs"   : "/docs",
    }


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}
