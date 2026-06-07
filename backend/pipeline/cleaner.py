"""
cleaner.py
──────────
Cleans comment text for sentiment analysis.

What is REMOVED:
  - URLs (http/https/www)
  - @mentions and #hashtags
  - HTML entities (&amp; &lt; etc.)
  - Repeated characters beyond 3 (sooooo → sooo)
  - Standalone numbers with no context
  - Non-semantic special characters (~^*|<>{}[])
  - Zero-width and invisible Unicode chars

What is KEPT / TRANSFORMED:
  - Emojis → sentiment text tags  (😍→[love], 👎→[bad])
  - ! and ? — sentiment bearing
  - Indian language punctuation (।)
  - Code-mixed words as-is

Input column used:
  `transliterated_text` if exists, else `text`

Adds column: `cleaned_text`

Reads : data/raw/merged_{lang}_raw.csv
Writes: data/processed/{lang}_processed.csv

Usage:
  python pipeline/cleaner.py
"""

import re
import html
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

try:
    import emoji as emoji_lib
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    print("  ⚠  emoji library not installed. Emojis will be stripped.")
    print("     Run: pip install emoji")

BASE_DIR   = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DIR       = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ── Emoji sentiment map ───────────────────────────────────────
# Most common emojis in Indian movie comment sections
EMOJI_SENTIMENT_MAP = {
    "😍": "[love]",   "🥰": "[love]",   "❤️": "[love]",
    "💯": "[perfect]","🔥": "[fire]",   "💪": "[strong]",
    "👏": "[applause]","🙌": "[applause]",
    "😂": "[funny]",  "🤣": "[funny]",
    "😭": "[crying]", "😢": "[sad]",
    "😡": "[angry]",  "🤬": "[angry]",  "😤": "[frustrated]",
    "👍": "[good]",   "👎": "[bad]",
    "💔": "[heartbroken]",
    "🤮": "[disgusting]","🤢": "[bad]",
    "⭐": "[star]",   "🌟": "[star]",
    "😴": "[boring]", "🥱": "[boring]",
    "😐": "[meh]",    "🙄": "[eyeroll]",
    "🎵": "[music]",  "🎶": "[music]",
    "🎬": "[movie]",  "🎭": "[drama]",
    "💥": "[blast]",  "✨": "[amazing]",
    "🚀": "[amazing]","😎": "[cool]",
    "🤩": "[amazing]","😱": "[shocked]",
}


# ── Regex patterns ────────────────────────────────────────────
URL_RE        = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE    = re.compile(r"@\w+")
HASHTAG_RE    = re.compile(r"#\w+")
HTML_TAG_RE   = re.compile(r"<[^>]+>")
SPECIAL_RE    = re.compile(r"[~^*|<>{}\[\]\\]")
MULTI_SPACE   = re.compile(r"\s{2,}")
REPEAT_CHAR   = re.compile(r"(.)\1{3,}")          # 4+ repeated chars
STANDALONE_NUM= re.compile(r"(?<!\w)\d+(?!\w)")
ZERO_WIDTH_RE = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]"
)


def replace_emojis(text: str) -> str:
    """Replace known sentiment emojis; remove unknown ones."""
    if not isinstance(text, str):
        return text

    result = []
    i = 0
    while i < len(text):
        # Try 2-char emoji first (e.g., ❤️ = ❤ + variation selector)
        two_char = text[i:i+2]
        one_char = text[i]

        if two_char in EMOJI_SENTIMENT_MAP:
            result.append(" " + EMOJI_SENTIMENT_MAP[two_char] + " ")
            i += 2
        elif one_char in EMOJI_SENTIMENT_MAP:
            result.append(" " + EMOJI_SENTIMENT_MAP[one_char] + " ")
            i += 1
        else:
            # Remove any remaining emoji using emoji library
            if EMOJI_AVAILABLE and emoji_lib.is_emoji(one_char):
                i += 1  # skip unknown emojis
            else:
                result.append(one_char)
                i += 1

    return "".join(result)


def clean_text(text: str) -> str:
    """Full cleaning pipeline for a single comment."""
    if not isinstance(text, str) or text.strip() == "":
        return ""

    # 1. Decode HTML entities
    text = html.unescape(text)

    # 2. Remove zero-width / invisible characters
    text = ZERO_WIDTH_RE.sub("", text)

    # 3. Remove HTML tags
    text = HTML_TAG_RE.sub(" ", text)

    # 4. Remove URLs
    text = URL_RE.sub(" ", text)

    # 5. Remove mentions and hashtags
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(" ", text)

    # 6. Replace emojis with sentiment tags
    text = replace_emojis(text)

    # 7. Remove non-semantic special characters
    text = SPECIAL_RE.sub(" ", text)

    # 8. Reduce repeated characters (soooo → sooo)
    text = REPEAT_CHAR.sub(r"\1\1\1", text)

    # 9. Normalize whitespace
    text = MULTI_SPACE.sub(" ", text).strip()

    return text


def is_too_short(text: str, min_tokens: int = 2) -> bool:
    """Flag very short cleaned comments as low-quality."""
    if not isinstance(text, str):
        return True
    tokens = [t for t in text.split() if len(t) > 1]
    return len(tokens) < min_tokens


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Text Cleaner")
    print("=" * 55)

    for lang in ["hindi", "telugu"]:
        in_path  = RAW_DIR / f"merged_{lang}_raw.csv"
        out_path = PROCESSED_DIR / f"{lang}_processed.csv"

        if not in_path.exists():
            print(f"\n  ⚠  File not found: {in_path.name}. Skipping.")
            continue

        print(f"\n── Processing: {lang.upper()} ──────────────────────────")
        df = pd.read_csv(in_path, encoding="utf-8-sig")

        # Use transliterated_text if available, fall back to text
        input_col = (
            "transliterated_text"
            if "transliterated_text" in df.columns
            else "text"
        )
        print(f"  Input column : {input_col}")

        tqdm.pandas(desc=f"  Cleaning ({lang})")
        df["cleaned_text"] = df[input_col].progress_apply(clean_text)

        # Flag short comments
        df["is_short"] = df["cleaned_text"].apply(is_too_short)
        short_count = df["is_short"].sum()
        print(f"  Short comments flagged : {short_count} ({short_count/len(df)*100:.1f}%)")

        # Stats
        empty_count = (df["cleaned_text"].str.strip() == "").sum()
        print(f"  Empty after cleaning   : {empty_count}")

        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  ✅ Saved {len(df)} rows → {out_path.relative_to(BASE_DIR)}")

    print(f"\n{'='*55}")
    print("  Cleaning complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
