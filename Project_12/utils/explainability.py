import os
import re


def _compute_grounding_score(query: str, docs) -> float:
  if not docs:
    return 0.0
  query_terms = set(re.findall(r"\w+", query.lower()))
  if not query_terms:
    return 0.0
  scores = []
  for doc in docs:
    content_terms = set(re.findall(r"\w+", doc.page_content.lower()))
    overlap = len(query_terms & content_terms)
    scores.append(overlap / max(1, len(query_terms)))
  return min(1.0, sum(scores) / len(scores))


class ExplainabilityEngine:

  def build_explanation(self, query, docs, reranked_docs, retrieval_scores=None):
    grounding = _compute_grounding_score(query, reranked_docs)
    grounding_pct = int(grounding * 100)

    lines = []
    lines.append(f"Grounding: {grounding_pct}%")
    lines.append("")
    lines.append("Sources:")

    for i, doc in enumerate(reranked_docs[:5]):
      source = doc.metadata.get("source", "Unknown")
      book = os.path.basename(str(source))
      page = doc.metadata.get("page", "N/A")
      chapter = doc.metadata.get("chapter", doc.metadata.get("section", "—"))
      score = retrieval_scores[i] if retrieval_scores and i < len(retrieval_scores) else None
      score_str = f" (score: {score:.3f})" if score is not None else ""
      lines.append(f"  {i + 1}. {book} — Chapter/Section: {chapter} — Page: {page}{score_str}")
      lines.append(f"     Chunk: {doc.page_content[:180]}...")

    lines.append("")
    lines.append("Retrieval: Hybrid (BM25 + FAISS) → Cross-encoder rerank")
    lines.append(f"Chunks retrieved: {len(docs)} → Reranked to: {len(reranked_docs)}")

    return "\n".join(lines), grounding_pct
