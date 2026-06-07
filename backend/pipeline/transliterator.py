"""
transliterator.py
─────────────────
Converts Roman-script Hindi/Telugu to their native scripts.

NOTE: ai4bharat-transliteration is incompatible with Python 3.12
(its dependency fairseq does not build). This module therefore runs
in FALLBACK MODE — Roman-script comments are passed through as-is.

MuRIL handles Roman-script (Romanized Hindi/Telugu) reasonably well
because it was trained on transliterated data, so sentiment accuracy
is not significantly impacted.

If you are on Python 3.9 or 3.10, you can install the library with:
  pip install ai4bharat-transliteration==1.1.4
and this module will automatically use it.

Adds column: `transliterated_text`
  - Same as input text (fallback mode on Python 3.12)

Reads/Writes : data/raw/merged_{lang}_raw.csv (in-place update)
"""

import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DIR = BASE_DIR / "data" / "raw"

LANG_MAP = {
    "hindi" : "hi",
    "telugu": "te",
}


def load_transliterator(lang_code: str):
    """
    Try to load AI4Bharat. Returns None if unavailable (Python 3.12).
    """
    try:
        from ai4bharat.transliteration import XlitEngine
        engine = XlitEngine(lang_code, beam_width=10, rescore=True)
        print("  ✓ AI4Bharat transliterator loaded successfully.")
        return engine
    except ImportError:
        print(
            "  ℹ  ai4bharat-transliteration not available on Python 3.12.\n"
            "     Running in fallback mode — Roman-script text kept as-is.\n"
            "     MuRIL handles Romanized Indian text natively, so sentiment\n"
            "     accuracy is not significantly affected."
        )
        return None
    except Exception as e:
        print(f"  ⚠  Transliterator load error: {e}. Using fallback mode.")
        return None


def transliterate_text(text: str, engine, lang_code: str) -> str:
    """Transliterate if engine available, else return original."""
    if engine is None or not isinstance(text, str) or text.strip() == "":
        return text

    import re
    words = text.split()
    result = []

    for word in words:
        if re.match(r"^[@#]|https?://|^\d+$", word):
            result.append(word)
            continue
        clean = re.sub(r"[^a-zA-Z]", "", word).lower()
        if not clean:
            result.append(word)
            continue
        try:
            transliterated = engine.translit_word(clean, lang_code, topk=1)
            if transliterated and transliterated[0]:
                suffix = re.sub(r"[a-zA-Z]", "", word)
                result.append(transliterated[0] + suffix)
            else:
                result.append(word)
        except Exception:
            result.append(word)

    return " ".join(result)


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Transliterator")
    print("=" * 55)

    for lang in ["hindi", "telugu"]:
        in_path   = RAW_DIR / f"merged_{lang}_raw.csv"
        lang_code = LANG_MAP[lang]

        if not in_path.exists():
            print(f"\n  ⚠  File not found: {in_path.name}. Skipping.")
            continue

        print(f"\n── Processing: {lang.upper()} ──────────────────────────")
        df = pd.read_csv(in_path, encoding="utf-8-sig")

        if "detected_lang" not in df.columns:
            print("  ⚠  Run language_detector.py first. Skipping.")
            continue

        mixed_mask  = df["detected_lang"] == "mixed_roman"
        mixed_count = mixed_mask.sum()
        print(f"  Roman-script rows found: {mixed_count}")

        # Try to load transliterator (will be None on Python 3.12)
        engine = load_transliterator(lang_code)

        # Default: transliterated_text = original text
        df["transliterated_text"] = df["text"]

        if engine is not None and mixed_count > 0:
            mixed_texts = df.loc[mixed_mask, "text"]
            tqdm.pandas(desc=f"  Transliterating ({lang})")
            df.loc[mixed_mask, "transliterated_text"] = \
                mixed_texts.progress_apply(
                    lambda t: transliterate_text(t, engine, lang_code)
                )
        elif mixed_count > 0:
            print(
                f"  Fallback: {mixed_count} Roman-script comments will be\n"
                f"  processed as-is by MuRIL (still effective for sentiment)."
            )

        df.to_csv(in_path, index=False, encoding="utf-8-sig")
        print(f"  ✅ Updated: {in_path.relative_to(BASE_DIR)}")

    print(f"\n{'='*55}")
    print("  Transliteration step complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
