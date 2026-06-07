"""
youtube_scraper.py
──────────────────
Fetches comments from one or more YouTube videos using the
YouTube Data API v3. Saves results to:
  data/raw/youtube_hindi_raw.csv
  data/raw/youtube_telugu_raw.csv

Usage:
  python scraper/youtube_scraper.py \
      --lang hindi \
      --video-ids "VIDEO_ID_1,VIDEO_ID_2"

  python scraper/youtube_scraper.py \
      --lang telugu \
      --video-ids "VIDEO_ID_3,VIDEO_ID_4"
"""

import os
import sys
import argparse
import time
import math
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

# ── Load env ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY   = os.getenv("YOUTUBE_API_KEY", "")
RAW_DIR   = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

MAX_RESULTS_PER_PAGE = 100   # YouTube API max per request
MAX_COMMENTS         = 5000  # safety cap per video


# ── Helpers ───────────────────────────────────────────────────

def get_youtube_client():
    if not API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY not set. Add it to backend/.env"
        )
    return build("youtube", "v3", developerKey=API_KEY)


def fetch_comments_for_video(youtube, video_id: str) -> list[dict]:
    """
    Pages through all top-level comments + replies for a video.
    Returns a list of flat comment dicts.
    """
    comments = []
    next_page_token = None

    pbar = tqdm(desc=f"  Video {video_id}", unit=" comments")

    while True:
        try:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=MAX_RESULTS_PER_PAGE,
                pageToken=next_page_token,
                textFormat="plainText",
                order="relevance",   # top comments first
            ).execute()
        except HttpError as e:
            if e.resp.status == 403:
                print(f"\n  ⚠  Comments disabled for video {video_id}. Skipping.")
            else:
                print(f"\n  ⚠  API error for {video_id}: {e}")
            break

        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "comment_id"  : item["snippet"]["topLevelComment"]["id"],
                "video_id"    : video_id,
                "author"      : top.get("authorDisplayName", ""),
                "text"        : top.get("textDisplay", ""),
                "like_count"  : int(top.get("likeCount", 0)),
                "reply_count" : int(item["snippet"].get("totalReplyCount", 0)),
                "published_at": top.get("publishedAt", ""),
                "source"      : "youtube",
            })
            pbar.update(1)

            # Fetch replies if any
            if item["snippet"].get("totalReplyCount", 0) > 0:
                replies = fetch_replies(youtube, item["id"], video_id)
                comments.extend(replies)
                pbar.update(len(replies))

        if len(comments) >= MAX_COMMENTS:
            print(f"\n  Reached {MAX_COMMENTS} comment cap for video {video_id}.")
            break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(0.1)   # gentle rate limiting

    pbar.close()
    return comments


def fetch_replies(youtube, parent_id: str, video_id: str) -> list[dict]:
    """Fetches all replies for a comment thread."""
    replies = []
    next_page_token = None

    while True:
        try:
            response = youtube.comments().list(
                part="snippet",
                parentId=parent_id,
                maxResults=MAX_RESULTS_PER_PAGE,
                pageToken=next_page_token,
                textFormat="plainText",
            ).execute()
        except HttpError:
            break

        for item in response.get("items", []):
            s = item["snippet"]
            replies.append({
                "comment_id"  : item["id"],
                "video_id"    : video_id,
                "author"      : s.get("authorDisplayName", ""),
                "text"        : s.get("textDisplay", ""),
                "like_count"  : int(s.get("likeCount", 0)),
                "reply_count" : 0,
                "published_at": s.get("publishedAt", ""),
                "source"      : "youtube",
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(0.1)

    return replies


def normalize_weights(df: pd.DataFrame) -> pd.DataFrame:
    """
    Log-normalize like_count to a 0-1 weight column.
    weight = log(1 + like_count) / log(1 + max_like_count)
    Falls back to 0.1 if all like counts are 0.
    """
    max_likes = df["like_count"].max()
    if max_likes == 0:
        df["weight"] = 0.1
    else:
        df["weight"] = df["like_count"].apply(
            lambda x: math.log1p(x) / math.log1p(max_likes)
        )
    # Ensure minimum weight so no comment is completely ignored
    df["weight"] = df["weight"].clip(lower=0.05)
    return df


# ── Main ──────────────────────────────────────────────────────

def run(lang: str, video_ids: list[str]):
    print(f"\n{'='*55}")
    print(f"  CinePulse-Indic | YouTube Scraper")
    print(f"  Language : {lang.upper()}")
    print(f"  Videos   : {len(video_ids)}")
    print(f"{'='*55}\n")

    if lang not in ("hindi", "telugu"):
        raise ValueError("--lang must be 'hindi' or 'telugu'")

    youtube = get_youtube_client()
    all_comments = []

    for vid in video_ids:
        vid = vid.strip()
        print(f"▶ Fetching comments from: https://youtu.be/{vid}")
        comments = fetch_comments_for_video(youtube, vid)
        print(f"  ✓ {len(comments)} comments fetched\n")
        all_comments.extend(comments)

    if not all_comments:
        print("No comments collected. Exiting.")
        sys.exit(0)

    df = pd.DataFrame(all_comments)

    # Tag the language community
    df["language_tag"] = lang

    # Drop exact duplicate comment IDs (same comment across video lists)
    before = len(df)
    df.drop_duplicates(subset=["comment_id"], keep="first", inplace=True)
    after = len(df)
    if before != after:
        print(f"  Dropped {before - after} duplicate comments.")

    # Normalize weights
    df = normalize_weights(df)

    # Save
    out_path = RAW_DIR / f"youtube_{lang}_raw.csv"
    # Append if file already exists (multiple scrape runs)
    if out_path.exists():
        existing = pd.read_csv(out_path)
        df = pd.concat([existing, df], ignore_index=True)
        df.drop_duplicates(subset=["comment_id"], keep="first", inplace=True)
        df = normalize_weights(df)   # re-normalize with full dataset

    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n{'='*55}")
    print(f"  ✅ Saved {len(df)} comments → {out_path.relative_to(BASE_DIR)}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CinePulse YouTube Scraper")
    parser.add_argument(
        "--lang",
        required=True,
        choices=["hindi", "telugu"],
        help="Language community of the video",
    )
    parser.add_argument(
        "--video-ids",
        required=True,
        help="Comma-separated YouTube video IDs (not full URLs)",
    )
    args = parser.parse_args()
    video_list = [v.strip() for v in args.video_ids.split(",") if v.strip()]
    run(args.lang, video_list)
