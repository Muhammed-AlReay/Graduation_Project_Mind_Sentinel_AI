#!/usr/bin/env python3
"""RAG verification with real retrieval, scores, and grounding %."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import RETRIEVAL_TOP_K, VECTORSTORE_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from utils.explainability import _compute_grounding_score

TEST_QUERIES = [
  "What is cognitive behavioral therapy?",
  "What are the symptoms of depression?",
  "How is anxiety treated?",
  "What is panic disorder?",
  "Tell me about PTSD treatment",
  "What causes schizophrenia?",
  "How does medication help bipolar disorder?",
  "What are the diagnostic criteria for major depressive disorder?",
  "How is OCD treated with exposure therapy?",
  "What is the difference between bipolar I and bipolar II?",
  "What are positive symptoms of schizophrenia?",
  "How long must GAD symptoms persist for diagnosis?",
  "What distinguishes PTSD from acute stress disorder?",
  "What is the hallmark cognitive deficit in delirium?",
  "How is borderline personality disorder characterized?",
  "What medications are used for social anxiety disorder?",
  "What are eating disorder warning signs?",
  "How does CBT treat insomnia?",
  "What is dissociative identity disorder?",
  "What are autism spectrum disorder core features?",
]


def main():
  if not VECTORSTORE_DIR.exists():
    print(json.dumps({"error": "vectorstore missing", "action": "python ingest.py"}))
    sys.exit(1)

  from langchain_huggingface import HuggingFaceEmbeddings
  from langchain_community.vectorstores import FAISS
  from service.loader import ServiceState

  state = ServiceState()
  state.initialize()

  results = []
  for query in TEST_QUERIES:
    docs = state.hybrid_retriever.get_relevant_documents(query)
    reranked = state.reranker.rerank(query, docs, top_k=RETRIEVAL_TOP_K)
    grounding = _compute_grounding_score(query, reranked)
    grounding_pct = int(grounding * 100)

    sources = []
    for i, doc in enumerate(reranked):
      sources.append({
        "rank": i + 1,
        "source": os.path.basename(str(doc.metadata.get("source", "Unknown"))),
        "page": doc.metadata.get("page"),
        "chunk_preview": doc.page_content[:200],
        "score": round(grounding, 4),
      })

    context = "\n\n".join(d.page_content for d in reranked)
    results.append({
      "query": query,
      "grounding_pct": grounding_pct,
      "meets_80_target": grounding_pct >= 80,
      "chunks_retrieved": len(docs),
      "chunks_reranked": len(reranked),
      "sources": sources,
      "context_length": len(context),
      "context_preview": context[:500],
    })

  avg_grounding = sum(r["grounding_pct"] for r in results) / len(results)
  report = {
    "timestamp": datetime.now().isoformat(),
    "config": {
      "chunk_size": CHUNK_SIZE,
      "chunk_overlap": CHUNK_OVERLAP,
      "embedding_model": EMBEDDING_MODEL,
      "retrieval_top_k": RETRIEVAL_TOP_K,
    },
    "queries": results,
    "avg_grounding_pct": round(avg_grounding, 1),
    "queries_above_80": sum(1 for r in results if r["meets_80_target"]),
  }

  out_dir = Path(__file__).parent.parent / "evaluation_results"
  out_dir.mkdir(exist_ok=True)
  out_file = out_dir / f"rag_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
  print(json.dumps(report, indent=2, ensure_ascii=False))
  print(f"\nSaved: {out_file}")


if __name__ == "__main__":
  main()
