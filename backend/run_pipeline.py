"""
run_pipeline.py
───────────────
Single entry point that runs the entire CinePulse-Indic
processing pipeline end-to-end.

Steps:
  1. merge_sources        ~1 min
  2. language_detector    ~2 min
  3. transliterator       ~3-5 min
  4. cleaner              ~1 min
  5. sentiment_engine     ~15-25 min (GPU) / ~60 min (CPU)
  6. aspect_extractor     ~20-30 min (GPU) / ~90 min (CPU)
  7. aggregator           ~1 min

Usage:
  python run_pipeline.py              # run all steps
  python run_pipeline.py --from 5    # resume from step 5
  python run_pipeline.py --only 7    # run only aggregator
"""

import sys
import json
import time
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR    = Path(__file__).resolve().parent
STATUS_FILE = BASE_DIR / "data" / "aggregated" / "pipeline_status.json"
STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)


def write_status(step: int, step_name: str, status: str,
                 error: str = "", elapsed: float = 0.0):
    """Write pipeline status to JSON — dashboard polls this."""
    data = {
        "current_step"  : step,
        "step_name"     : step_name,
        "status"        : status,       # running | done | error | idle
        "error"         : error,
        "elapsed_sec"   : round(elapsed, 1),
        "updated_at"    : datetime.now(timezone.utc).isoformat(),
        "total_steps"   : 7,
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_step(step_num: int, step_name: str, module_path: str):
    """Import and run a pipeline module, track timing + status."""
    print(f"\n{'━'*55}")
    print(f"  Step {step_num}/7 — {step_name}")
    print(f"{'━'*55}")

    write_status(step_num, step_name, "running")
    start = time.time()

    try:
        # Dynamically import and run the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            step_name, BASE_DIR / module_path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run()

        elapsed = time.time() - start
        write_status(step_num, step_name, "done", elapsed=elapsed)
        print(f"\n  ⏱  Step {step_num} completed in {elapsed:.1f}s")

    except Exception as e:
        elapsed = time.time() - start
        err_msg = traceback.format_exc()
        write_status(step_num, step_name, "error",
                     error=str(e), elapsed=elapsed)
        print(f"\n  ✗ Step {step_num} FAILED: {e}")
        print(err_msg)
        raise


STEPS = [
    (1, "Merge Sources",       "pipeline/merge_sources.py"),
    (2, "Language Detection",  "pipeline/language_detector.py"),
    (3, "Transliteration",     "pipeline/transliterator.py"),
    (4, "Text Cleaning",       "pipeline/cleaner.py"),
    (5, "Sentiment Analysis",  "pipeline/sentiment_engine.py"),
    (6, "Aspect Extraction",   "pipeline/aspect_extractor.py"),
    (7, "Aggregation",         "pipeline/aggregator.py"),
]


def main():
    parser = argparse.ArgumentParser(
        description="CinePulse-Indic Pipeline Runner"
    )
    parser.add_argument(
        "--from", dest="from_step", type=int, default=1,
        help="Resume from step N (default: 1)",
    )
    parser.add_argument(
        "--only", dest="only_step", type=int, default=None,
        help="Run only step N",
    )
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  CinePulse-Indic | Full Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    write_status(0, "starting", "running")
    total_start = time.time()

    steps_to_run = STEPS

    if args.only_step:
        steps_to_run = [s for s in STEPS if s[0] == args.only_step]
        if not steps_to_run:
            print(f"  ✗ Invalid step number: {args.only_step}")
            sys.exit(1)
    elif args.from_step > 1:
        steps_to_run = [s for s in STEPS if s[0] >= args.from_step]

    for step_num, step_name, module_path in steps_to_run:
        run_step(step_num, step_name, module_path)

    total_elapsed = time.time() - total_start
    write_status(7, "Pipeline Complete", "done", elapsed=total_elapsed)

    print(f"\n{'='*55}")
    print(f"  ✅ Pipeline complete in {total_elapsed/60:.1f} minutes")
    print(f"  Dashboard data ready in: backend/data/aggregated/")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
