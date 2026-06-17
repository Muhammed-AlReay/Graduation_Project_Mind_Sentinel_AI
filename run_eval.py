import os
import time
import json
from datetime import datetime

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

from llm_router import get_llm
from config import VECTORSTORE_DIR, EMBEDDING_MODEL

from evaluation.dataset import dataset
from evaluation.evaluator import run_rag_evaluation


# =========================
# BUILD RAG CHAIN (EVAL VERSION)
# =========================
def build_rag_chain():

    if not os.path.exists(VECTORSTORE_DIR):
        raise FileNotFoundError("Vector store not found")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    vectorstore = FAISS.load_local(
        VECTORSTORE_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    # تقليل عدد الوثائق لتقليل التوكنز
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 4}
    )

    llm = get_llm()

    # =========================
    # Context Rewriting
    # =========================
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", "Rewrite question to be standalone."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever,
        contextualize_prompt
    )

    # =========================
    # SYSTEM PROMPT
    # =========================
    system_prompt = (
        "You are an experienced, professional, and compassionate psychiatric medical assistant.\n"
        " Always produce clean, professional, and visually organized responses, Use clear Markdown formatting to improve readability, Use bullet points for lists and step-by-step recommendations, Use numbered lists for instructions, action plans, assessments, and treatment recommendations , Use spacing effectively between sections.\n"
        " When presenting comparisons, symptoms, risks, treatment options, assessments, progress tracking, or structured information, use professional Markdown tables, Ensure tables have clear column names, Keep table content concise and readable, Align information logically, Do not create unnecessarily large tables,  Use tables only when they improve understanding.\n"
        "Your role is to provide accurate, clear, and supportive mental health information while maintaining a warm and reassuring tone.\n" 
        "Use the following retrieved context as your primary source when answering the user's question.\n" 
        "Respond in a way that feels natural, professional, and patient-centered, Provide educational mental health information, Do  diagnose, Do not claim certainty, Encourage professional help when appropriate.\n" 
        " Use emojis sparingly to improve warmth and engagement,Use bold text for important observations and key recommendations,Highlight emergency or safety information clearly.\n" 
        "Keep explanations clear and easy to understand, and organize information using short paragraphs or bullet points when appropriate .\n"
        "The assistant has broad knowledge of psychological and psychiatric conditions beyond the disorders explicitly listed in the Knowledge Areas section.\n"
        "The assistant may recognize symptom patterns that are consistent with less common, rare, emerging, unspecified, or culture-related mental health conditions when supported by the user's reported experiences.\n"
        "The assistant can discuss possible psychological, psychiatric, behavioral, emotional, developmental, cognitive, trauma-related, addiction-related, and neurocognitive conditions, including conditions not explicitly listed in the Knowledge Areas section.\n"
        "When discussing mental health conditions, explain symptoms, causes, diagnosis, treatments, or related information when available in the context.\n" 
        "If the provided context does not contain sufficient information to fully answer the question, politely state:\n" 
        "The required information is not available in my reference books.\n" 
        "In such cases, provide only the information supported by the context and avoid making unsupported claims.\n" 
        "Do not invent facts, create references, or present uncertain information as certain.\n" 
        "Maintain a professional, empathetic, and trustworthy tone throughout the conversation.\n\n" 
        "Use ONLY the following context:\n\n" 
        "Context:\n{context}")


    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    qa_chain = create_stuff_documents_chain(
        llm,
        qa_prompt
    )

    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        qa_chain
    )

    return rag_chain


# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":

    print("=" * 60)
    print("🚀 RAG Evaluation System")
    print("=" * 60)

    start_time = time.time()

    # =========================
    # Reduce Dataset During Testing
    # =========================
    dataset = dataset[:20]

    rag_chain = build_rag_chain()

    print(
        f"\n📊 Running evaluation on {len(dataset)} questions...\n"
    )

    try:

        ragas_scores, results = run_rag_evaluation(
            rag_chain,
            dataset
        )

    except Exception as e:

        print("\n❌ Evaluation Failed")
        print(str(e))

        ragas_scores = {}
        results = []

    # =========================
    # RESULTS
    # =========================
    print("\n========== FINAL RAGAS SCORE ==========\n")

    if ragas_scores:

        for metric, value in ragas_scores.items():

            print(
                f"{metric:<25}: {value:.4f}"
            )

    else:

        print("No metrics generated.")

    # =========================
    # SAVE RESULTS
    # =========================
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    file_name = (
        f"ragas_evaluation_{timestamp}.json"
    )

    with open(
        file_name,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            ragas_scores,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"\n💾 Saved -> {file_name}")

    print(
        f"\n⏱ Time: "
        f"{round(time.time() - start_time, 2)} sec"
    )

    print("\n✅ Evaluation Completed Successfully")