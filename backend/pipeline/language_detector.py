"""
language_detector.py
────────────────────
Detects the script/language of each comment and tags it.

Tags assigned:
  hi           → Devanagari Hindi
  te           → Telugu script
  en           → English
  mixed_roman  → Roman-script Hindi or Telugu (needs transliteration)
  unknown      → Too short or undetectable

Reads  : data/raw/merged_{lang}_raw.csv
Writes : adds column `detected_lang` in place (same file is passed
         forward; the column is appended)

Usage:
  python pipeline/language_detector.py
"""

import re
import pandas as pd
from pathlib import Path
from langdetect import detect, LangDetectException
from langdetect import DetectorFactory
from tqdm import tqdm
from dotenv import load_dotenv

# Make langdetect deterministic
DetectorFactory.seed = 42

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DIR  = BASE_DIR / "data" / "raw"

# ── Unicode range helpers ─────────────────────────────────────

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")   # Hindi script
TELUGU_RE     = re.compile(r"[\u0C00-\u0C7F]")   # Telugu script
ROMAN_RE      = re.compile(r"[a-zA-Z]")


def detect_script(text: str) -> str:
    """
    Primary detection via Unicode script ranges — fast and
    reliable for Indian scripts.
    Falls back to langdetect for Roman-script text.
    """
    if not isinstance(text, str) or len(text.strip()) < 3:
        return "unknown"

    has_devanagari = bool(DEVANAGARI_RE.search(text))
    has_telugu     = bool(TELUGU_RE.search(text))
    has_roman      = bool(ROMAN_RE.search(text))

    # Pure Indian scripts
    if has_devanagari and not has_roman:
        return "hi"
    if has_telugu and not has_roman:
        return "te"

    # Mixed Indian script + Roman (code-mixing) — treat as native
    if has_devanagari and has_roman:
        return "hi"
    if has_telugu and has_roman:
        return "te"

    # Pure Roman — use langdetect to decide
    if has_roman:
        return detect_roman(text)

    return "unknown"


def detect_roman(text: str) -> str:
    """
    For Roman-script text, use langdetect to guess if it's
    English or Roman-transliterated Indian language.
    Returns 'en', 'mixed_roman', or 'unknown'.
    """
    try:
        lang = detect(text)
        if lang == "en":
            return "en"
        # langdetect may detect hi/te even in Roman script
        if lang in ("hi", "te"):
            return "mixed_roman"
        # Other Indian languages in Roman script
        if lang in ("mr", "gu", "kn", "ml", "ta", "pa", "bn"):
            return "mixed_roman"
        # For very short or ambiguous text, tag as mixed_roman
        # if it contains common Indian words
        if contains_indic_words(text):
            return "mixed_roman"
        return "en"
    except LangDetectException:
        return "unknown"


# Common Roman-script Indian words that langdetect may miss
INDIC_ROMAN_WORDS = {
    # Hindi
    "kya", "hai", "nahi", "bahut", "accha", "acha", "bhai",
    "yaar", "toh", "mast", "ekdum", "ek", "dum", "seedha",
    "bakwaas", "kek", "keka", "maja", "maza", "bilkul",
    # Telugu
    "keka", "baaga", "chala", "chusa", "movie", "ante",
    "inka", "super", "thaman", "dsp", "mass", "pawan",
    "kalyan", "allu", "arjun", "tollywood", "bollywood",
}


def contains_indic_words(text: str) -> bool:
    words = set(text.lower().split())
    return bool(words & INDIC_ROMAN_WORDS)


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Language Detector")
    print("=" * 55)

    for lang in ["hindi", "telugu"]:
        in_path = RAW_DIR / f"merged_{lang}_raw.csv"
        if not in_path.exists():
            print(f"\n  ⚠  File not found: {in_path.name}. Skipping.")
            continue

        print(f"\n── Processing: {lang.upper()} ──────────────────────────")
        df = pd.read_csv(in_path, encoding="utf-8-sig")

        tqdm.pandas(desc="  Detecting languages")
        df["detected_lang"] = df["text"].progress_apply(detect_script)

        # Stats
        counts = df["detected_lang"].value_counts()
        print(f"\n  Language distribution:")
        for tag, cnt in counts.items():
            pct = cnt / len(df) * 100
            print(f"    {tag:<15}: {cnt:>5}  ({pct:.1f}%)")

        df.to_csv(in_path, index=False, encoding="utf-8-sig")
        print(f"\n  ✅ Updated: {in_path.relative_to(BASE_DIR)}")

    print(f"\n{'='*55}")
    print("  Language detection complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
