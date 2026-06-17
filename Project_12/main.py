import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage, HumanMessage

from utils.explainability import ExplainabilityEngine

from safety.safety_guard import SafetyGuard
from safety.crisis_handler import CrisisHandler

from llm_router import get_llm
from config import VECTORSTORE_DIR, EMBEDDING_MODEL

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker

from memory.memory_manager import MemoryManager

# =========================
# 🔥 WRAPPER (Mتمسحهوش)
# =========================
class HybridLangChainRetriever:
    def __init__(self, hybrid_retriever, reranker):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker

    def get_relevant_documents(self, query: str):
        docs = self.hybrid_retriever.get_relevant_documents(query)
        docs = self.reranker.rerank(query, docs, top_k=7)
        return docs


def main():

    # =========================
    # PATIENT LOGIN
    # =========================

    print("=" * 50)
    print("Mental Health Assistant")
    print("=" * 50)

    print("1. New Patient")
    print("2. Login With Patient ID")
    print("3. Login With Email")

    choice = input(
        "\nChoose option (1/2): "
    )

    if choice == "1":

        name = input("Name: ")
        age = input("Age: ")
        gender = input("Gender: ")
        email = input("Email: ")
        password = input("Password: ")
        
        if MemoryManager.email_already_exists(email):
            print("\nEmail already exists.")
            return

        patient_id = MemoryManager.create_new_patient(
            name,
            age,
            gender,
            email,
            password
        )

        print("\n" + "=" * 50)
        print("Your Patient ID:")
        print(patient_id)
        print("Please save this ID carefully.")
        print("=" * 50)

    elif choice == "2":

        patient_id = input(
            "Enter Patient ID: "
        )

    elif choice == "3":
        email = input("Email: ")

        password = input("Password: ")

        patient_id = MemoryManager.login_by_email(
            email,
            password
        )

        if not patient_id:

            print("Invalid email or password")
            return    

    else:

        print("Invalid choice")
        return

    memory = MemoryManager(
        patient_id
    )
    session_id = memory.start_session()

    profile = memory.get_profile()

    if not profile:

        print("Patient ID not found.")
        return

    print(
        f"\nWelcome back {profile['name']}"
    )

    # =========================
    # Load Vector Store
    # =========================
    if not VECTORSTORE_DIR.exists():
        print("Vector store not found. Please run 'python ingest.py' first.")
        return

    print("Loading local vector store...")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vectorstore = FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    # =========================
    # Docs for BM25 (Mتمسحهوش)
    # =========================
    docs = list(vectorstore.docstore._dict.values())

    # =========================
    # MEMORY CONTEXT
    # =========================

    memory_context = ""

    if profile:

        memory_context += (
            "\n\nKnown User Information:\n"
            + str(profile)
        )

    # =========================
    # Hybrid + Reranker
    # =========================
    hybrid_retriever = HybridRetriever(vectorstore, docs)
    reranker = Reranker()

    final_retriever = HybridLangChainRetriever(hybrid_retriever, reranker)

    # =========================
    # LLM
    # =========================
    print("Initializing LLM Router...")
    llm = get_llm()
    # =========================
    # SAFETY
    # =========================
    safety_guard = SafetyGuard(llm)
    crisis_handler = CrisisHandler()
    # =========================
    # 🔥 EXPLAINABILITY (ADDED ONLY)
    # =========================
    explain_engine = ExplainabilityEngine()

    # # =========================
    # # MEMORY
    # # =========================

    # print("\nAvailable Users:")
    # users = memory.list_users()

    # if users:
    #     for i, user in enumerate(users, start=1):
    #         print(f"{i}. {user}")

    # print("\n1. Existing User")
    # print("2. New User")

    # choice = input("\nSelect option (1/2): ")

    # if choice == "1" and users:

    #     user_id = input("Enter user id: ").strip()

    # else:

    #     user_id = input("Create user id: ").strip()

    #     memory.create_user(user_id)

    # print(f"\nLoaded Memory For: {user_id}")

    # chat_history = memory.load_chat_history(user_id)

    # profile = memory.get_profile(user_id)

    # =========================
    # Contextualization Prompt
    # =========================

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    # =========================
    # History aware retriever
    # =========================
    # history_aware_retriever = create_history_aware_retriever(
    #     llm,
    #     final_retriever,
    #     contextualize_q_prompt
    # )

    # =========================
    # SYSTEM PROMPT (FIXED)
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
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    # =========================
    # RAG CHAIN
    # =========================
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # rag_chain = create_retrieval_chain(
    #     history_aware_retriever,
    #     question_answer_chain
    # )

    # =========================
    # Chat Loop
    # =========================
    print("\nSystem Ready. Type 'exit' or 'quit' to stop.")
    print("-" * 50)

    chat_history = []

    while True:

        user_input = input("\nEnter your question: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        if not user_input.strip():
            continue

        try:
            # =========================
            # SAFETY CHECK
            # =========================

            category = safety_guard.classify(user_input)

            safety_response = None

            if category != "SAFE":

                safety_response = crisis_handler.get_response(category)

                if safety_response is None:

                    safety_response = (
                        "I'm here to help. Could you tell me a little more about what you're experiencing?"
                    )

            # 2. Retrieval (Hybrid + Rerank)
            docs = hybrid_retriever.get_relevant_documents(user_input)
            docs = reranker.rerank(user_input, docs, top_k=7)

            #context = "\n\n".join([d.page_content for d in docs])
            context = "\n\n".join([d.page_content for d in docs])
            context += memory_context

            # 3. LLM call with proper messages
            filled_system = system_prompt.replace("{context}", context)
            response = llm.invoke([
                SystemMessage(content=filled_system),
                *chat_history,
                HumanMessage(content=user_input)
            ])
            

            answer = response.content

            # =========================
            # COMBINE SAFETY + LLM
            # =========================

            final_answer = ""

            if safety_response:

                final_answer += (
                    "⚠️ Safety Guidance:\n"
                    + safety_response
                    + "\n\n"
                )

            final_answer += (
                "🤖 Assistant Response:\n"
                + answer
            )

            # =========================
            # SAVE MEMORY
            # =========================

            memory.save_user_message(user_input)

            memory.save_assistant_message(final_answer)

            memory.add_session_message(session_id, "user", user_input)
            memory.add_session_message(session_id, "assistant", final_answer)

            memory.save_qa_record(
                user_input,
                final_answer
            )

            memory.add_concern(user_input)
            memory.add_note(final_answer)

            profile = memory.get_profile()

            # =========================
            # 🔥 EXPLAINABILITY (ADDED ONLY HERE)
            # =========================
            explanation = explain_engine.build_explanation(
                user_input,
                docs,
                docs  # reranked same list (no change in logic)
            )

            print("\nAnswer:")
            print(final_answer)

            print("\n" + "=" * 50)
            print("EXPLANATION")
            print("=" * 50)
            print(explanation)

            print("\nSources Used:")
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "Unknown")
                file_name = os.path.basename(source)
                print(f"- {file_name} (Page: {page})")

            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=final_answer))
            

            

            

        except Exception as e:
            print(f"\nError: {e}")



if __name__ == "__main__":
    main()