"""
routes/report.py
────────────────
Triggers PDF report generation and returns the file
as a downloadable response.
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

router   = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AGG_DIR  = BASE_DIR / "data" / "aggregated"


@router.get("/report/download")
def download_report():
    """
    Generates the PDF report and returns it as a download.
    """
    # Lazy import to avoid loading ReportLab unless needed
    from report.report_generator import generate_pdf

    out_path = AGG_DIR / "dhurandhar_report.pdf"

    try:
        report_data_path  = AGG_DIR / "dhurandhar_report_data.json"
        scores_path       = AGG_DIR / "dhurandhar_scores.json"

        if not report_data_path.exists() or not scores_path.exists():
            return JSONResponse(
                status_code=404,
                content={"detail": "Run the pipeline first before downloading report."},
            )

        with open(report_data_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        with open(scores_path, "r", encoding="utf-8") as f:
            scores_data = json.load(f)

        generate_pdf(report_data, scores_data, str(out_path))

        return FileResponse(
            path        = str(out_path),
            filename    = "CinePulse_Dhurandhar_Report.pdf",
            media_type  = "application/pdf",
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Report generation failed: {str(e)}"},
        )
