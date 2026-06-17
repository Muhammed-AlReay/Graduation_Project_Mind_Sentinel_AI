#!/usr/bin/env python3
"""
Phase 7: Baseline evaluation before RAG parameter changes.
Stores metrics for before/after comparison.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.multilingual_parity_dataset import run_crisis_parity_test
from safety.heuristic_classifier import heuristic_crisis_classify

# Inline crisis safety accuracy (no LLM needed for heuristic baseline)
def crisis_safety_accuracy():
  from evaluation.multilingual_parity_dataset import CRISIS_PARITY_CASES
  correct = 0
  for text, expected in CRISIS_PARITY_CASES:
    if heuristic_crisis_classify(text) == expected:
      correct += 1
  return correct / len(CRISIS_PARITY_CASES) if CRISIS_PARITY_CASES else 0


def main():
  print("=" * 60)
  print("BASELINE EVALUATION — Phase 7")
  print("=" * 60)

  baseline = {
    "timestamp": datetime.now().isoformat(),
    "rag_config": {
      "chunk_size": 1200,
      "chunk_overlap": 200,
      "note": "Unchanged — evaluation required before modification",
    },
    "crisis_parity": run_crisis_parity_test(),
    "safety_accuracy": crisis_safety_accuracy(),
    "crisis_accuracy": crisis_safety_accuracy(),
    "ragas_metrics": {
      "note": "Run `python run_eval.py` with OPENROUTER_API_KEY for full RAGAS metrics",
      "faithfulness": None,
      "context_precision": None,
      "context_recall": None,
      "answer_relevancy": None,
      "answer_correctness": None,
    },
    "arabic_english_parity": run_crisis_parity_test()["accuracy"],
  }

  # Load prior RAGAS results if available
  p12 = Path(__file__).resolve().parent.parent
  ragas_files = sorted(p12.glob("ragas_evaluation_*.json"), reverse=True)
  if ragas_files:
    try:
      prior = json.loads(ragas_files[0].read_text(encoding="utf-8"))
      baseline["ragas_metrics"] = {**baseline["ragas_metrics"], **prior}
      baseline["ragas_metrics"]["source_file"] = ragas_files[0].name
    except Exception:
      pass

  out_dir = p12 / "evaluation_results"
  out_dir.mkdir(exist_ok=True)
  out_file = out_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  out_file.write_text(json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8")

  print(json.dumps(baseline, indent=2, ensure_ascii=False))
  print(f"\nSaved baseline: {out_file}")


if __name__ == "__main__":
  main()
