from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings


class HybridRetriever:
    def __init__(self, vectorstore, documents):
        # Dense (FAISS)
        self.dense_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 20}
        )

        # BM25 (keyword search)
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 20

    def get_relevant_documents(self, query: str):
        dense_docs = self.dense_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query)

        # merge
        all_docs = dense_docs + bm25_docs

        # remove duplicates
        seen = set()
        unique_docs = []

        for doc in all_docs:
            key = doc.page_content
            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

        return unique_docs[:20]