from langchain_openai import ChatOpenAI

from config import MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


def get_llm():
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_agentrouter_api_key_here":
        raise ValueError("Please set a valid OPENROUTER_API_KEY in the environment")

    return ChatOpenAI(
        model_name=MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=0.6,
    )