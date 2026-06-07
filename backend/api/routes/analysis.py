"""
routes/analysis.py
──────────────────
Endpoints for aggregated sentiment data and pipeline status.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router  = APIRouter()
AGG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "aggregated"


def load_json(filename: str) -> dict:
    path = AGG_DIR / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{filename} not found. "
                "Run the pipeline first: python run_pipeline.py"
            ),
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/overview")
def get_overview():
    """
    Returns overall + per-aspect sentiment scores for both languages.
    Powers: SentimentCards, AspectRadar, AspectBarChart.
    """
    return load_json("dhurandhar_scores.json")


@router.get("/timeline")
def get_timeline():
    """
    Returns daily-bucketed sentiment scores for both languages.
    Powers: SentimentTimeline chart.
    """
    return load_json("dhurandhar_timeline.json")


@router.get("/report-data")
def get_report_data():
    """
    Returns gap analysis, top comments per aspect, recommendations.
    Powers: PDF report generation and the Recommendations panel.
    """
    return load_json("dhurandhar_report_data.json")


@router.get("/status")
def get_pipeline_status():
    """
    Returns current pipeline run status.
    Polled by the frontend to show a progress indicator.
    """
    status_path = AGG_DIR / "pipeline_status.json"
    if not status_path.exists():
        return {
            "status"      : "idle",
            "step_name"   : "Not started",
            "current_step": 0,
            "total_steps" : 7,
        }
    with open(status_path, "r") as f:
        return json.load(f)
