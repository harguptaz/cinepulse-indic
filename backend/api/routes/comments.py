"""
routes/comments.py
──────────────────
Paginated, filterable comment feed from the aspects CSV files.
Powers: CommentFeed table on the dashboard.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Literal
from fastapi import APIRouter, Query, HTTPException

router      = APIRouter()
ASPECTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "aspects"

VALID_ASPECTS = [
    "acting", "audio", "technical", "plot",
    "dub_quality", "direction", "general",
]
VALID_SENTIMENTS = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
VALID_LANGS      = ["hindi", "telugu"]


def load_aspects_df(lang: Optional[str] = None) -> pd.DataFrame:
    """Load one or both language aspect CSVs."""
    frames = []
    langs  = [lang] if lang else VALID_LANGS

    for l in langs:
        path = ASPECTS_DIR / f"{l}_aspects.csv"
        if path.exists():
            df = pd.read_csv(path, encoding="utf-8-sig")
            df["language"] = l
            frames.append(df)

    if not frames:
        raise HTTPException(
            status_code=404,
            detail="No aspect data found. Run the pipeline first.",
        )
    return pd.concat(frames, ignore_index=True)


@router.get("/comments")
def get_comments(
    lang     : Optional[str] = Query(None, description="hindi | telugu"),
    aspect   : Optional[str] = Query(None, description="acting | audio | ..."),
    sentiment: Optional[str] = Query(None, description="POSITIVE | NEGATIVE | NEUTRAL"),
    source   : Optional[str] = Query(None, description="youtube | reddit"),
    page     : int           = Query(1, ge=1),
    page_size: int           = Query(20, ge=1, le=100),
):
    """
    Returns a paginated, filtered list of comments with their
    sentiment and aspect labels.
    """
    # Validate filters
    if lang and lang not in VALID_LANGS:
        raise HTTPException(400, f"lang must be one of {VALID_LANGS}")
    if aspect and aspect not in VALID_ASPECTS:
        raise HTTPException(400, f"aspect must be one of {VALID_ASPECTS}")
    if sentiment and sentiment.upper() not in VALID_SENTIMENTS:
        raise HTTPException(400, f"sentiment must be one of {VALID_SENTIMENTS}")

    df = load_aspects_df(lang)

    # Apply filters
    if aspect:
        df = df[df["primary_aspect"] == aspect]
    if sentiment:
        df = df[df["sentiment_label"] == sentiment.upper()]
    if source:
        df = df[df["source"] == source.lower()]

    total = len(df)

    # Sort by weight descending
    df = df.sort_values("weight", ascending=False)

    # Paginate
    start = (page - 1) * page_size
    end   = start + page_size
    page_df = df.iloc[start:end]

    # Select columns to return
    cols = [
        "comment_id", "text", "language", "source",
        "sentiment_label", "sentiment_confidence",
        "primary_aspect", "secondary_aspect",
        "weight", "published_at",
    ]
    # Only include columns that exist
    cols = [c for c in cols if c in page_df.columns]

    records = page_df[cols].fillna("").to_dict(orient="records")

    return {
        "total"      : total,
        "page"       : page,
        "page_size"  : page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "comments"   : records,
    }


@router.get("/comments/stats")
def get_comment_stats():
    """
    Quick stats about total comments per language and source.
    """
    df = load_aspects_df()
    stats = {}

    for lang in VALID_LANGS:
        sub = df[df["language"] == lang] if "language" in df.columns else pd.DataFrame()
        if sub.empty:
            stats[lang] = {"total": 0}
            continue

        stats[lang] = {
            "total"  : int(len(sub)),
            "sources": sub["source"].value_counts().to_dict()
                       if "source" in sub.columns else {},
        }

    return stats
