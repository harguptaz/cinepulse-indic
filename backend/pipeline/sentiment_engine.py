"""
sentiment_engine.py
───────────────────
Runs multilingual sentiment analysis on each cleaned comment.

Model: cardiffnlp/twitter-xlm-roberta-base-sentiment
  - Fine-tuned for 3-class sentiment: Positive / Negative / Neutral
  - Trained on multilingual Twitter/social media data
  - Handles informal text, code-mixed Hindi/Telugu, emojis-as-text
  - Works out of the box — no fine-tuning required

Why NOT MuRIL base (google/muril-base-cased)?
  MuRIL base is a masked language model with NO pre-trained
  classification head. Its classifier.bias and classifier.weight
  are randomly initialized, producing near-random logits that
  cluster around 0.5/0.5, falling below the neutral threshold
  and labelling every comment as NEUTRAL.

Adds columns:
  sentiment_label        → POSITIVE | NEGATIVE | NEUTRAL
  sentiment_confidence   → float 0.0–1.0
  weighted_score         → direction × confidence × weight

Reads : data/processed/{lang}_processed.csv
Writes: data/sentiment/{lang}_sentiment.csv

Usage:
  python pipeline/sentiment_engine.py

Model download (~1.1 GB, first run only):
  python -c "
  from transformers import AutoTokenizer, AutoModelForSequenceClassification
  name = 'cardiffnlp/twitter-xlm-roberta-base-sentiment'
  AutoTokenizer.from_pretrained(name).save_pretrained('models/twitter-xlm-roberta-sentiment')
  AutoModelForSequenceClassification.from_pretrained(name).save_pretrained('models/twitter-xlm-roberta-sentiment')
  print('Saved.')
  "
"""

import os
import torch
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from transformers import pipeline as hf_pipeline

BASE_DIR      = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PROCESSED_DIR = BASE_DIR / "data" / "processed"
SENTIMENT_DIR = BASE_DIR / "data" / "sentiment"
SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE     = os.getenv("DEVICE", "cpu")
BATCH_SIZE = int(os.getenv("SENTIMENT_BATCH_SIZE", "16"))
MAX_LENGTH = 128

MODEL_NAME  = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
LOCAL_MODEL = BASE_DIR / "models" / "twitter-xlm-roberta-sentiment"

# ── Label normalisation ───────────────────────────────────────
LABEL_MAP = {
    "positive": "POSITIVE", "negative": "NEGATIVE", "neutral": "NEUTRAL",
    "LABEL_2":  "POSITIVE", "LABEL_0":  "NEGATIVE", "LABEL_1": "NEUTRAL",
    "pos":      "POSITIVE", "neg":      "NEGATIVE", "neu":     "NEUTRAL",
}


class SentimentEngine:
    def __init__(self):
        model_source = str(LOCAL_MODEL) if LOCAL_MODEL.exists() else MODEL_NAME
        print(f"  Loading model : {model_source}")
        print(f"  Device        : {DEVICE}")

        device_id = 0 if DEVICE == "cuda" and torch.cuda.is_available() else -1

        self.classifier = hf_pipeline(
            "text-classification",
            model=model_source,
            tokenizer=model_source,
            device=device_id,
            max_length=MAX_LENGTH,
            truncation=True,
            top_k=1,
        )
        print("  ✓ Model loaded\n")

    def normalise_label(self, raw: str) -> str:
        return LABEL_MAP.get(raw.lower(), LABEL_MAP.get(raw, "NEUTRAL"))

    def predict_batch(self, texts: list) -> list:
        if not texts:
            return []
        safe = [t if t.strip() else "neutral" for t in texts]
        try:
            results = self.classifier(safe, batch_size=BATCH_SIZE)
        except Exception as e:
            print(f"  ⚠  Batch error: {e}. Marking batch as NEUTRAL.")
            return [{"sentiment_label": "NEUTRAL",
                     "sentiment_confidence": 0.5}] * len(texts)

        output = []
        for res in results:
            item  = res[0] if isinstance(res, list) else res
            label = self.normalise_label(item["label"])
            score = round(float(item["score"]), 4)
            output.append({"sentiment_label": label,
                           "sentiment_confidence": score})
        return output

    def run_on_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        texts         = df["cleaned_text"].fillna("").tolist()
        all_results   = []
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in tqdm(range(0, len(texts), BATCH_SIZE),
                      desc="  Sentiment inference",
                      unit=" batches", total=total_batches):
            all_results.extend(self.predict_batch(texts[i: i + BATCH_SIZE]))

        result_df = pd.DataFrame(all_results)
        df        = pd.concat([df.reset_index(drop=True), result_df], axis=1)

        direction_map        = {"POSITIVE": 1, "NEGATIVE": -1, "NEUTRAL": 0}
        df["direction"]      = df["sentiment_label"].map(direction_map)
        df["weighted_score"] = (
            df["direction"] * df["sentiment_confidence"] * df["weight"]
        ).round(6)
        df.drop(columns=["direction"], inplace=True)
        return df


def run():
    print("=" * 55)
    print("  CinePulse-Indic | Sentiment Engine")
    print(f"  Model: {MODEL_NAME}")
    print("=" * 55)

    engine = SentimentEngine()

    for lang in ["hindi", "telugu"]:
        in_path  = PROCESSED_DIR / f"{lang}_processed.csv"
        out_path = SENTIMENT_DIR  / f"{lang}_sentiment.csv"

        if not in_path.exists():
            print(f"\n  ⚠  {in_path.name} not found. Skipping.")
            continue

        print(f"\n── Processing: {lang.upper()} ──────────────────────────")
        df = pd.read_csv(in_path, encoding="utf-8-sig")
        print(f"  Rows: {len(df)}")
        df = engine.run_on_dataframe(df)

        counts = df["sentiment_label"].value_counts()
        print(f"\n  Sentiment distribution:")
        for label, cnt in counts.items():
            pct = cnt / len(df) * 100
            print(f"    {label:<12}: {cnt:>5}  ({pct:.1f}%)")

        avg = df["weighted_score"].mean()
        print(f"\n  Avg weighted score : {avg:+.4f}")
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  ✅ Saved → {out_path.relative_to(BASE_DIR)}")

    print(f"\n{'='*55}")
    print("  Sentiment analysis complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
