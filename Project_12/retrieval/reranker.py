from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL


class Reranker:
    def __init__(self):
        self.model = CrossEncoder(RERANKER_MODEL)

    def rerank(self, query, documents, top_k=7):
        pairs = [(query, doc.page_content) for doc in documents]

        scores = self.model.predict(pairs)

        scored_docs = list(zip(documents, scores))

        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored_docs[:top_k]]