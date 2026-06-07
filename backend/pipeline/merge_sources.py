"""
merge_sources.py
────────────────
Merges YouTube API CSV and Reddit Web-Scraper CSV for each
language into a single unified CSV with consistent schema.

Input files expected:
  data/raw/youtube_hindi_raw.csv
  data/raw/youtube_telugu_raw.csv
  data/raw/reddit_hindi_raw.csv      (optional)
  data/raw/reddit_telugu_raw.csv     (optional)

Output:
  data/raw/merged_hindi_raw.csv
  data/raw/merged_telugu_raw.csv

Usage:
  python pipeline/merge_sources.py
"""

import re
import math
import hashlib
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DIR = BASE_DIR / "data" / "raw"

# ── Unified output schema ─────────────────────────────────────
UNIFIED_COLS = [
    "comment_id",
    "text",
    "author",
    "published_at",
    "post_title",
    "source",        # "youtube" | "reddit"
    "like_count",
    "weight",
    "language_tag",
]


# ── Reddit column mappings ────────────────────────────────────
# Web Scraper exports with varying column names.
# Map all known variants to our standard names.
REDDIT_COL_MAP = {
    # comment text variants
    "comment-text"        : "text",
    "comment_text"        : "text",
    "Comment Text"        : "text",
    "comment text"        : "text",
    "body"                : "text",
    "content"             : "text",

    # author variants
    "author"              : "author",
    "Author"              : "author",
    "author-text"         : "author",
    "username"            : "author",
    "user"                : "author",

    # timestamp variants
    "timestamp"           : "published_at",
    "Timestamp"           : "published_at",
    "time"                : "published_at",
    "date"                : "published_at",
    "published_at"        : "published_at",
    "created_at"          : "published_at",

    # post title variants
    "post-title"          : "post_title",
    "post_title"          : "post_title",
    "Post Title"          : "post_title",
    "title"               : "post_title",
    "thread_title"        : "post_title",
}


def make_comment_id(text: str, source: str, author: str) -> str:
    """Generate a stable ID for comments that don't have one."""
    raw = f"{source}|{author}|{text[:100]}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def normalize_reddit_df(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    """
    Rename Web Scraper columns → unified schema.
    Reddit comments get weight = 1.0 (no upvote data).
    """
    # Rename whatever columns exist
    rename = {k: v for k, v in REDDIT_COL_MAP.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Ensure all required columns exist
    for col in ["text", "author", "published_at", "post_title"]:
        if col not in df.columns:
            df[col] = ""

    # Drop rows with empty comment text
    df = df[df["text"].notna() & (df["text"].str.strip() != "")]

    df["source"]       = "reddit"
    df["like_count"]   = 0
    df["weight"]       = 1.0         # uniform weight — no upvote data
    df["language_tag"] = lang

    # Generate comment IDs
    df["comment_id"] = df.apply(
        lambda r: make_comment_id(
            str(r.get("text", "")),
            "reddit",
            str(r.get("author", ""))
        ),
        axis=1,
    )

    return df[UNIFIED_COLS]


def normalize_youtube_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    YouTube CSV already has the right schema from youtube_scraper.py.
    Just align to unified columns.
    """
    if "post_title" not in df.columns:
        df["post_title"] = ""

    # Ensure weight column exists (re-normalize if needed)
    if "weight" not in df.columns or df["weight"].isna().all():
        max_likes = df["like_count"].max() if "like_count" in df.columns else 0
        if max_likes > 0:
            df["weight"] = df["like_count"].apply(
                lambda x: math.log1p(x) / math.log1p(max_likes)
            )
        else:
            df["weight"] = 0.1
        df["weight"] = df["weight"].clip(lower=0.05)

    df = df[df["text"].notna() & (df["text"].str.strip() != "")]
    return df[UNIFIED_COLS]


def merge_for_language(lang: str):
    print(f"\n── Merging sources for: {lang.upper()} ──────────────────")

    yt_path     = RAW_DIR / f"youtube_{lang}_raw.csv"
    reddit_path = RAW_DIR / f"reddit_{lang}_raw.csv"
    out_path    = RAW_DIR / f"merged_{lang}_raw.csv"

    frames = []

    # YouTube
    if yt_path.exists():
        yt_df = pd.read_csv(yt_path, encoding="utf-8-sig")
        yt_df = normalize_youtube_df(yt_df)
        frames.append(yt_df)
        print(f"  ✓ YouTube   : {len(yt_df):>5} comments loaded")
    else:
        print(f"  ⚠  YouTube file not found: {yt_path.name}")

    # Reddit
    if reddit_path.exists():
        reddit_df = pd.read_csv(reddit_path, encoding="utf-8-sig")
        reddit_df = normalize_reddit_df(reddit_df, lang)
        frames.append(reddit_df)
        print(f"  ✓ Reddit    : {len(reddit_df):>5} comments loaded")
    else:
        print(f"  ℹ  Reddit file not found (optional): {reddit_path.name}")

    if not frames:
        print(f"  ✗ No data files found for {lang}. Skipping.")
        return

    merged = pd.concat(frames, ignore_index=True)

    # Deduplicate by comment_id
    before = len(merged)
    merged.drop_duplicates(subset=["comment_id"], keep="first", inplace=True)
    after = len(merged)
    if before != after:
        print(f"  Dropped {before - after} duplicate comment IDs.")

    # Final sort by date
    merged["published_at"] = pd.to_datetime(
        merged["published_at"], errors="coerce", utc=True
    )
    merged.sort_values("published_at", inplace=True, na_position="last")

    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  ✅ Saved {len(merged)} comments → {out_path.relative_to(BASE_DIR)}")

    # Source breakdown
    src_counts = merged["source"].value_counts()
    for src, cnt in src_counts.items():
        print(f"     {src:<12}: {cnt}")


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Source Merger")
    print("=" * 55)

    for lang in ["hindi", "telugu"]:
        merge_for_language(lang)

    print(f"\n{'='*55}")
    print("  Merge complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
