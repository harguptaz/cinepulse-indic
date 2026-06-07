"""
aspect_extractor.py
───────────────────
Performs Aspect-Based Sentiment Analysis (ABSA) using
facebook/bart-large-mnli for zero-shot classification.

Each comment is assigned:
  primary_aspect            → top matching aspect
  primary_aspect_confidence → NLI score for primary aspect
  secondary_aspect          → second aspect if score within 0.10 of primary
                              (or "none")

Aspect taxonomy:
  acting     → Acting and character performance
  audio      → Background music, songs, and sound design
  technical  → Visual effects, cinematography, and editing
  plot       → Story, screenplay, and climax
  dub_quality→ Dubbing quality and voice cast
  direction  → Direction, pacing, and overall filmmaking
  general    → Fallback when no aspect exceeds confidence threshold

Reads : data/sentiment/{lang}_sentiment.csv
Writes: data/aspects/{lang}_aspects.csv

Usage:
  python pipeline/aspect_extractor.py
"""

import os
import torch
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from transformers import pipeline

BASE_DIR     = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SENTIMENT_DIR = BASE_DIR / "data" / "sentiment"
ASPECTS_DIR   = BASE_DIR / "data" / "aspects"
ASPECTS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE       = os.getenv("DEVICE", "cpu")
CONF_THR     = float(os.getenv("ASPECT_CONFIDENCE_THRESHOLD", "0.45"))
SECONDARY_GAP = 0.10    # secondary aspect within this gap of primary
BATCH_SIZE    = 16      # smaller batches — BART is heavy
MODEL_NAME    = "facebook/bart-large-mnli"

# ── Aspect definitions ────────────────────────────────────────
ASPECTS = {
    "acting"     : "acting and character performance by the cast",
    "audio"      : "background music, songs, and sound design",
    "technical"  : "visual effects, cinematography, and editing",
    "plot"       : "story, screenplay, narrative, and climax",
    "dub_quality": "dubbing quality, voice acting, and lip sync",
    "direction"  : "direction, pacing, and overall filmmaking",
}

ASPECT_LABELS  = list(ASPECTS.values())
ASPECT_KEYS    = list(ASPECTS.keys())
LABEL_TO_KEY   = {v: k for k, v in ASPECTS.items()}


class AspectExtractor:
    def __init__(self):
        device_id = 0 if DEVICE == "cuda" and torch.cuda.is_available() else -1
        print(f"  Loading model : {MODEL_NAME}")
        print(f"  Device        : {'cuda' if device_id == 0 else 'cpu'}")
        self.classifier = pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
            device=device_id,
        )
        print("  ✓ Model loaded\n")

    def classify_batch(self, texts: list[str]) -> list[dict]:
        """
        Classify a batch of texts against all aspect labels.
        Returns list of {primary_aspect, primary_aspect_confidence,
                         secondary_aspect} dicts.
        """
        if not texts:
            return []

        # Zero-shot classifier handles batching internally
        outputs = self.classifier(
            texts,
            candidate_labels=ASPECT_LABELS,
            multi_label=False,
            batch_size=BATCH_SIZE,
        )

        # Normalize single-text output to list
        if isinstance(outputs, dict):
            outputs = [outputs]

        results = []
        for output in outputs:
            labels = output["labels"]   # sorted by score desc
            scores = output["scores"]

            top_label = labels[0]
            top_score = scores[0]

            # Primary aspect
            if top_score >= CONF_THR:
                primary_key  = LABEL_TO_KEY[top_label]
                primary_conf = round(top_score, 4)
            else:
                primary_key  = "general"
                primary_conf = round(top_score, 4)

            # Secondary aspect (only if within gap of primary)
            secondary_key = "none"
            if len(labels) > 1 and primary_key != "general":
                second_score = scores[1]
                if (top_score - second_score) <= SECONDARY_GAP:
                    secondary_key = LABEL_TO_KEY[labels[1]]

            results.append({
                "primary_aspect"            : primary_key,
                "primary_aspect_confidence" : primary_conf,
                "secondary_aspect"          : secondary_key,
            })

        return results

    def run_on_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        texts = df["cleaned_text"].fillna("").tolist()
        texts = [t if t.strip() else "general comment" for t in texts]

        all_results = []
        batch_count = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in tqdm(
            range(0, len(texts), BATCH_SIZE),
            desc="  Aspect extraction",
            unit=" batches",
            total=batch_count,
        ):
            batch = texts[i : i + BATCH_SIZE]
            results = self.classify_batch(batch)
            all_results.extend(results)

        result_df = pd.DataFrame(all_results)
        df = df.reset_index(drop=True)
        df = pd.concat([df, result_df], axis=1)
        return df


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Aspect Extractor (BART zero-shot)")
    print("=" * 55)

    extractor = AspectExtractor()

    for lang in ["hindi", "telugu"]:
        in_path  = SENTIMENT_DIR / f"{lang}_sentiment.csv"
        out_path = ASPECTS_DIR   / f"{lang}_aspects.csv"

        if not in_path.exists():
            print(f"\n  ⚠  File not found: {in_path.name}. Skipping.")
            continue

        print(f"\n── Processing: {lang.upper()} ──────────────────────────")
        df = pd.read_csv(in_path, encoding="utf-8-sig")
        print(f"  Rows to process: {len(df)}")

        df = extractor.run_on_dataframe(df)

        # Aspect distribution
        counts = df["primary_aspect"].value_counts()
        print(f"\n  Aspect distribution:")
        for aspect, cnt in counts.items():
            pct = cnt / len(df) * 100
            print(f"    {aspect:<15}: {cnt:>5}  ({pct:.1f}%)")

        # Per-aspect sentiment breakdown
        print(f"\n  Per-aspect sentiment:")
        for aspect in list(ASPECTS.keys()) + ["general"]:
            mask = df["primary_aspect"] == aspect
            if mask.sum() == 0:
                continue
            sub = df[mask]
            pos = (sub["sentiment_label"] == "POSITIVE").sum()
            neg = (sub["sentiment_label"] == "NEGATIVE").sum()
            neu = (sub["sentiment_label"] == "NEUTRAL").sum()
            total = len(sub)
            print(
                f"    {aspect:<15}: "
                f"+{pos/total*100:.0f}% "
                f"-{neg/total*100:.0f}% "
                f"~{neu/total*100:.0f}%"
            )

        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n  ✅ Saved → {out_path.relative_to(BASE_DIR)}")

    print(f"\n{'='*55}")
    print("  Aspect extraction complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
