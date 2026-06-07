"""
aggregator.py
─────────────
Reads per-comment aspect + sentiment data and produces
three dashboard-ready JSON files:

  data/aggregated/dhurandhar_scores.json
    → Overall + per-aspect scores per language

  data/aggregated/dhurandhar_timeline.json
    → Daily weighted sentiment scores for timeline chart

  data/aggregated/dhurandhar_report_data.json
    → Top comments per aspect, gap analysis, recommendations

Usage:
  python pipeline/aggregator.py
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

BASE_DIR     = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ASPECTS_DIR  = BASE_DIR / "data" / "aspects"
AGG_DIR      = BASE_DIR / "data" / "aggregated"
AGG_DIR.mkdir(parents=True, exist_ok=True)

MOVIE_NAME   = os.getenv("MOVIE_NAME", "Dhurandhar")
RELEASE_DATE = os.getenv("MOVIE_RELEASE_DATE", "2025-06-05")

ALL_ASPECTS = [
    "acting", "audio", "technical",
    "plot", "dub_quality", "direction", "general",
]


# ── Helper ────────────────────────────────────────────────────

def safe_pct(part, total):
    return round(part / total * 100, 2) if total > 0 else 0.0

def weighted_sentiment_score(df_sub: pd.DataFrame) -> float:
    """
    Weighted average sentiment score in [-1, +1].
    weighted_score column already encodes direction × conf × weight.
    """
    total_weight = df_sub["weight"].sum()
    if total_weight == 0:
        return 0.0
    raw = df_sub["weighted_score"].sum() / total_weight
    return round(float(np.clip(raw, -1.0, 1.0)), 4)


def compute_aspect_block(df: pd.DataFrame, aspect: str) -> dict:
    """Compute sentiment breakdown for a single aspect."""
    sub = df[df["primary_aspect"] == aspect]
    total = len(sub)
    if total == 0:
        return {
            "comment_count"          : 0,
            "positive_pct"           : 0.0,
            "negative_pct"           : 0.0,
            "neutral_pct"            : 0.0,
            "weighted_sentiment_score": 0.0,
        }

    pos = (sub["sentiment_label"] == "POSITIVE").sum()
    neg = (sub["sentiment_label"] == "NEGATIVE").sum()
    neu = (sub["sentiment_label"] == "NEUTRAL").sum()

    return {
        "comment_count"          : int(total),
        "positive_pct"           : safe_pct(pos, total),
        "negative_pct"           : safe_pct(neg, total),
        "neutral_pct"            : safe_pct(neu, total),
        "weighted_sentiment_score": weighted_sentiment_score(sub),
    }


def compute_language_block(df: pd.DataFrame) -> dict:
    """Full stats for one language."""
    total = len(df)
    pos   = (df["sentiment_label"] == "POSITIVE").sum()
    neg   = (df["sentiment_label"] == "NEGATIVE").sum()
    neu   = (df["sentiment_label"] == "NEUTRAL").sum()

    source_counts = df["source"].value_counts().to_dict()

    aspects_data = {}
    for aspect in ALL_ASPECTS:
        aspects_data[aspect] = compute_aspect_block(df, aspect)

    return {
        "total_comments"          : int(total),
        "source_breakdown"        : {k: int(v) for k, v in source_counts.items()},
        "overall": {
            "positive_pct"            : safe_pct(pos, total),
            "negative_pct"            : safe_pct(neg, total),
            "neutral_pct"             : safe_pct(neu, total),
            "weighted_sentiment_score": weighted_sentiment_score(df),
        },
        "aspects": aspects_data,
    }


def build_scores_json(dfs: dict) -> dict:
    """Build dhurandhar_scores.json"""
    languages = {}
    for lang, df in dfs.items():
        languages[lang] = compute_language_block(df)

    return {
        "movie"       : MOVIE_NAME,
        "release_date": RELEASE_DATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "languages"   : languages,
    }


def build_timeline_json(dfs: dict) -> dict:
    """
    Build daily-bucketed timeline data.
    Each entry: { date, hindi_score, telugu_score,
                  hindi_volume, telugu_volume }
    """
    daily = {}

    for lang, df in dfs.items():
        df = df.copy()
        df["published_at"] = pd.to_datetime(
            df["published_at"], errors="coerce", utc=True
        )
        df = df.dropna(subset=["published_at"])
        df["date_str"] = df["published_at"].dt.strftime("%Y-%m-%d")

        for date_str, group in df.groupby("date_str"):
            if date_str not in daily:
                daily[date_str] = {}

            score = weighted_sentiment_score(group)
            daily[date_str][f"{lang}_score"]  = score
            daily[date_str][f"{lang}_volume"] = int(len(group))

    # Build sorted list
    timeline = []
    for date_str in sorted(daily.keys()):
        entry = {"date": date_str}
        entry.update(daily[date_str])
        # Fill missing languages with 0
        for lang in ["hindi", "telugu"]:
            entry.setdefault(f"{lang}_score",  0.0)
            entry.setdefault(f"{lang}_volume", 0)
        timeline.append(entry)

    return {"movie": MOVIE_NAME, "timeline": timeline}


def get_top_comments(df: pd.DataFrame, aspect: str,
                     sentiment: str, n: int = 3) -> list[dict]:
    """Get top N weighted comments for an aspect + sentiment."""
    sub = df[
        (df["primary_aspect"] == aspect) &
        (df["sentiment_label"] == sentiment)
    ].copy()

    if sub.empty:
        return []

    sub = sub.sort_values("weight", ascending=False)
    results = []
    for _, row in sub.head(n).iterrows():
        results.append({
            "text"      : str(row.get("text", ""))[:300],
            "weight"    : round(float(row.get("weight", 0)), 4),
            "confidence": round(float(row.get("sentiment_confidence", 0)), 4),
            "source"    : str(row.get("source", "")),
        })
    return results


def generate_recommendations(gap_analysis: list) -> list[str]:
    """
    Auto-generate recommendation strings from aspect gaps.
    A recommendation is triggered when an aspect score < 0.3
    or when a language-gap > 0.3.
    """
    recs = []
    for item in gap_analysis:
        aspect = item["aspect"]
        hi_score = item.get("hindi_score", 0)
        te_score = item.get("telugu_score", 0)
        gap      = item.get("gap", 0)

        aspect_label = aspect.replace("_", " ").title()

        if hi_score < 0.3 and hi_score != 0:
            recs.append(
                f"Hindi audience expressed concerns about {aspect_label}. "
                f"Consider revisiting this aspect for future releases targeting "
                f"the Hindi market."
            )
        if te_score < 0.3 and te_score != 0:
            recs.append(
                f"Telugu audience expressed concerns about {aspect_label}. "
                f"Improvements here could significantly boost reception in the "
                f"Telugu market."
            )
        if gap > 0.3:
            better  = "Hindi" if hi_score > te_score else "Telugu"
            weaker  = "Telugu" if hi_score > te_score else "Hindi"
            recs.append(
                f"Significant gap in {aspect_label} sentiment between "
                f"{better} (positive) and {weaker} (negative) communities. "
                f"Localisation or targeted improvements recommended for "
                f"the {weaker} version."
            )

    if not recs:
        recs.append(
            "Overall sentiment is strong across both language communities. "
            "No critical concerns identified."
        )
    return recs


def build_report_json(dfs: dict, scores: dict) -> dict:
    """Build dhurandhar_report_data.json"""
    top_comments = {}
    gap_analysis = []

    for aspect in ALL_ASPECTS:
        if aspect == "general":
            continue
        top_comments[aspect] = {}
        for lang, df in dfs.items():
            top_comments[aspect][lang] = {
                "positive": get_top_comments(df, aspect, "POSITIVE"),
                "negative": get_top_comments(df, aspect, "NEGATIVE"),
            }

        hi_score = (
            scores["languages"].get("hindi", {})
            .get("aspects", {})
            .get(aspect, {})
            .get("weighted_sentiment_score", 0)
        )
        te_score = (
            scores["languages"].get("telugu", {})
            .get("aspects", {})
            .get(aspect, {})
            .get("weighted_sentiment_score", 0)
        )
        gap = abs(hi_score - te_score)
        gap_analysis.append({
            "aspect"      : aspect,
            "hindi_score" : hi_score,
            "telugu_score": te_score,
            "gap"         : round(gap, 4),
        })

    # Sort by gap descending
    gap_analysis.sort(key=lambda x: x["gap"], reverse=True)

    return {
        "movie"           : MOVIE_NAME,
        "generated_at"    : datetime.now(timezone.utc).isoformat(),
        "gap_analysis"    : gap_analysis,
        "top_comments"    : top_comments,
        "recommendations" : generate_recommendations(gap_analysis),
    }


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Aggregator")
    print("=" * 55)

    dfs = {}
    for lang in ["hindi", "telugu"]:
        path = ASPECTS_DIR / f"{lang}_aspects.csv"
        if path.exists():
            dfs[lang] = pd.read_csv(path, encoding="utf-8-sig")
            print(f"  ✓ Loaded {lang}: {len(dfs[lang])} rows")
        else:
            print(f"  ⚠  {path.name} not found. Skipping {lang}.")

    if not dfs:
        print("  No data to aggregate. Run the pipeline first.")
        return

    # ── Scores JSON ───────────────────────────────────────────
    scores = build_scores_json(dfs)
    scores_path = AGG_DIR / "dhurandhar_scores.json"
    with open(scores_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ Scores    → {scores_path.relative_to(BASE_DIR)}")

    # ── Timeline JSON ─────────────────────────────────────────
    timeline = build_timeline_json(dfs)
    timeline_path = AGG_DIR / "dhurandhar_timeline.json"
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Timeline  → {timeline_path.relative_to(BASE_DIR)}")

    # ── Report JSON ───────────────────────────────────────────
    report = build_report_json(dfs, scores)
    report_path = AGG_DIR / "dhurandhar_report_data.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Report    → {report_path.relative_to(BASE_DIR)}")

    # ── Quick summary ─────────────────────────────────────────
    print(f"\n  {'─'*40}")
    print(f"  SUMMARY — {MOVIE_NAME}")
    print(f"  {'─'*40}")
    for lang, data in scores["languages"].items():
        ov = data["overall"]
        print(
            f"  {lang.upper():<10} "
            f"Total: {data['total_comments']:>5}  "
            f"+{ov['positive_pct']:.1f}% "
            f"-{ov['negative_pct']:.1f}% "
            f"~{ov['neutral_pct']:.1f}%  "
            f"Score: {ov['weighted_sentiment_score']:+.3f}"
        )

    print(f"\n{'='*55}")
    print("  Aggregation complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
