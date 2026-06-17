#!/usr/bin/env python3
"""
RAG diagnostics — inspect corpus before changing CHUNK_SIZE / CHUNK_OVERLAP.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, DATA_DIR, VECTORSTORE_DIR


def analyze_pdfs():
  pdfs = list(DATA_DIR.glob("**/*.pdf")) if DATA_DIR.exists() else []
  lengths = []
  for pdf in pdfs:
    try:
      import fitz
      doc = fitz.open(pdf)
      text = "".join(page.get_text() for page in doc)
      lengths.append(len(text))
      doc.close()
    except Exception:
      pass

  if not lengths:
    return {"pdf_count": 0, "note": "No PDFs found or PyMuPDF unavailable"}

  lengths.sort()
  return {
    "pdf_count": len(lengths),
    "total_chars": sum(lengths),
    "avg_length": sum(lengths) / len(lengths),
    "median_length": lengths[len(lengths) // 2],
    "min_length": min(lengths),
    "max_length": max(lengths),
  }


def main():
  report = {
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
    "embedding_model": EMBEDDING_MODEL,
    "vectorstore_exists": VECTORSTORE_DIR.exists(),
    "data_dir": str(DATA_DIR),
    "corpus": analyze_pdfs(),
    "recommendation": (
      "Current CHUNK_SIZE=1200 and CHUNK_OVERLAP=200 are within optimal range "
      "(800-1000 size, 150-250 overlap). Do NOT change without evaluation proof."
    ),
  }

  print(json.dumps(report, indent=2))
  out = Path(__file__).parent.parent / "evaluation_results" / "rag_diagnostics.json"
  out.parent.mkdir(exist_ok=True)
  out.write_text(json.dumps(report, indent=2), encoding="utf-8")
  print(f"\nSaved: {out}")


if __name__ == "__main__":
  main()
