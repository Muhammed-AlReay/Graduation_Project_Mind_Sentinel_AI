"""RAG chat orchestration extracted from the CLI main loop."""
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import RETRIEVAL_TOP_K
from memory.memory_manager import MemoryManager
from pipeline.translation import TranslationLayer
from pipeline.unified_pipeline import build_pipeline_context
from safety.crisis_policy import apply_crisis_policy
from service.loader import ServiceState
from service.models import ChatMessage, ChatResponse, SourceDocument

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
  "You are an experienced, professional, and compassionate psychiatric medical assistant.\n"
  "Your role is to provide accurate, clear, and supportive mental health information while maintaining a warm and reassuring tone.\n"
  "Use the following retrieved context as your primary source when answering the user's question.\n"
  "Respond in a way that feels natural, professional, and patient-centered. Provide educational mental health information. "
  "Do not diagnose. Do not claim certainty. Encourage professional help when appropriate.\n"
  "Keep explanations clear and easy to understand, and organize information using short paragraphs or bullet points when appropriate.\n"
  "When discussing mental health conditions, explain symptoms, causes, diagnosis, treatments, or related information when available in the context.\n"
  "If the provided context does not contain sufficient information to fully answer the question, politely state:\n"
  "The required information is not available in my reference books.\n"
  "Do not invent facts, create references, or present uncertain information as certain.\n"
  "Maintain a professional, empathetic, and trustworthy tone throughout the conversation.\n"
  "You may use contextual emojis sparingly when they add warmth (e.g. reassurance), but never spam them.\n\n"
  "Use ONLY the following context:\n\n"
  "Context:\n{context}"
)

CRISIS_SYSTEM_PROMPT_EN = (
  "You are Dr. Sentinel, a compassionate mental health assistant in CRISIS MODE.\n"
  "The user has expressed suicide risk, self-harm, or acute distress.\n"
  "Rules — absolute:\n"
  "- Acknowledge their pain first. Be warm, brief, and present.\n"
  "- Prioritize safety. Encourage contacting a crisis line or trusted person NOW.\n"
  "- US: 988. Egypt: 16328. Encourage local emergency services if immediate danger.\n"
  "- Do NOT lecture, diagnose, or give long educational content.\n"
  "- Do NOT minimize feelings. Do NOT use clinical jargon.\n"
  "- Offer one simple grounding step if appropriate (slow breath).\n"
  "- Stay engaged — ask if they are safe right now.\n"
  "- Reply entirely in English.\n"
)

CRISIS_SYSTEM_PROMPT_AR = (
  "أنت د. سنتينيل، مساعد دعم نفسي في وضع الأزمة.\n"
  "المستخدم عبّر عن خطر انتحار أو إيذاء ذاتي أو ضيق حاد.\n"
  "قواعد — مطلقة:\n"
  "- اعترف بألمه أولاً. كن دافئاً ومختصراً وحاضراً.\n"
  "- الأولوية للسلامة. شجّع على الاتصال بخط أزمة أو شخص موثوق الآن.\n"
  "- مصر: 16328. شجّع على الطوارئ إذا كان هناك خطر فوري.\n"
  "- لا تلقّح ولا تشخّص ولا تقدّم محتوى تعليمي طويل.\n"
  "- لا تقلّل من مشاعره. لا تستخدم مصطلحات سريرية.\n"
  "- قدّم خطوة تهدئة بسيطة واحدة إن لزم (تنفس بطيء).\n"
  "- ابقَ متواصلاً — اسأل إن كانوا بأمان الآن.\n"
  "- اكتب بالكامل بالعربية.\n"
)

_executor = ThreadPoolExecutor(max_workers=4)


def _is_arabic(text: str) -> bool:
  if not text:
    return False
  ar = len(re.findall(r"[\u0600-\u06FF]", text))
  en = len(re.findall(r"[a-zA-Z]", text))
  return ar >= en and ar > 0


def _log_crisis_event(category: str) -> None:
  if category == "SUICIDE_RISK":
    logger.info('{"component":"chat_service","event":"SUICIDE_DETECTED"}')
  elif category == "SELF_HARM":
    logger.info('{"component":"chat_service","event":"SELF_HARM_DETECTED"}')
  elif category != "SAFE":
    logger.info('{"component":"chat_service","event":"CRISIS_PIPELINE_ACTIVATED","category":"%s"}', category)


def _docs_to_sources(docs) -> list[SourceDocument]:
  sources = []
  for doc in docs:
    source = doc.metadata.get("source", "Unknown")
    page = doc.metadata.get("page", None)
    sources.append(
      SourceDocument(
        content=doc.page_content[:500],
        source=os.path.basename(str(source)),
        page=page,
      )
    )
  return sources


def _run_with_timeout(fn, timeout: int):
  future = _executor.submit(fn)
  try:
    return future.result(timeout=timeout)
  except FuturesTimeoutError:
    future.cancel()
    raise TimeoutError(f"Operation timed out after {timeout}s")


def process_chat(
  state: ServiceState,
  message: str,
  patient_id: str | None = None,
  chat_history: list[ChatMessage] | None = None,
  include_explanation: bool = False,
  persist_memory: bool = True,
) -> ChatResponse:
  chat_history = chat_history or []
  memory = None
  memory_context = ""

  if patient_id:
    memory = MemoryManager(patient_id)
    profile = memory.get_profile()
    if profile:
      memory_context = "\n\nKnown User Information:\n" + str(profile)

  translator = TranslationLayer(state.llm)

  def build_context():
    return build_pipeline_context(message, state.safety_guard, translator)

  try:
    ctx = _run_with_timeout(build_context, state.llm_timeout)
  except Exception as exc:
    logger.error('{"component":"chat_service","event":"PIPELINE_FAILED","stage":"context","error":"%s"}', type(exc).__name__)
    category = state.safety_guard.classify(message)
    ctx = None

  if ctx:
    category = ctx.safety_category
    policy = ctx.crisis_policy
    rag_query = ctx.canonical_english
    user_lang = ctx.detected_language
  else:
    category = state.safety_guard.classify(message)
    policy = apply_crisis_policy(category)
    rag_query = message
    user_lang = "en" if not _is_arabic(message) else "ar"

  if category != "SAFE":
    _log_crisis_event(category)

  safety_guidance = None
  if policy["use_safety_response"]:
    safety_guidance = state.crisis_handler.get_response(category, message)

  is_crisis = policy["crisis_mode"]
  docs = []

  if is_crisis and policy["skip_normal_rag"]:
    crisis_system = CRISIS_SYSTEM_PROMPT_AR if _is_arabic(message) else CRISIS_SYSTEM_PROMPT_EN
    filled_system = crisis_system
    if safety_guidance:
      filled_system += f"\n\nSafety guidance template (incorporate naturally, do not copy verbatim labels):\n{safety_guidance}"
  else:
    def retrieve():
      docs_inner = state.hybrid_retriever.get_relevant_documents(rag_query)
      return state.reranker.rerank(rag_query, docs_inner, top_k=RETRIEVAL_TOP_K)

    try:
      docs = _run_with_timeout(retrieve, state.llm_timeout)
    except Exception as exc:
      logger.error('{"component":"chat_service","event":"RAG_RETRIEVAL_FAILED","error":"%s"}', type(exc).__name__)
      docs = []

    if is_crisis:
      crisis_system = CRISIS_SYSTEM_PROMPT_AR if _is_arabic(message) else CRISIS_SYSTEM_PROMPT_EN
      filled_system = crisis_system
      if safety_guidance:
        filled_system += f"\n\nSafety guidance template (incorporate naturally, do not copy verbatim labels):\n{safety_guidance}"
      if docs and policy["allow_rag"]:
        rag_context = "\n\n".join(d.page_content for d in docs)
        filled_system += f"\n\nSupplemental reference context (educational only, crisis response takes priority):\n{rag_context}"
    else:
      context = "\n\n".join(d.page_content for d in docs) + memory_context
      filled_system = SYSTEM_PROMPT.replace("{context}", context)

  history_messages = []
  for msg in chat_history[-20:]:
    if msg.role == "user":
      history_messages.append(HumanMessage(content=msg.content))
    else:
      history_messages.append(AIMessage(content=msg.content))

  def generate():
    return state.llm.invoke([
      SystemMessage(content=filled_system),
      *history_messages,
      HumanMessage(content=message),
    ])

  try:
    response = _run_with_timeout(generate, state.llm_timeout)
    answer_text = response.content
  except Exception as exc:
    logger.error('{"component":"chat_service","event":"CRISIS_PIPELINE_FAILED","stage":"generate","error":"%s"}', type(exc).__name__)
    if is_crisis and safety_guidance:
      answer_text = safety_guidance
    else:
      raise

  final_answer = answer_text
  if user_lang != "en" and translator:
    try:
      final_answer = _run_with_timeout(
        lambda: translator.from_english(answer_text, user_lang),
        state.llm_timeout,
      )
    except Exception as exc:
      logger.warning('{"component":"chat_service","event":"TRANSLATION_BACK_FAILED","error":"%s"}', type(exc).__name__)

  if is_crisis and safety_guidance and safety_guidance not in final_answer:
    final_answer = safety_guidance + "\n\n" + final_answer

  if persist_memory and memory:
    try:
      memory.save_user_message(message)
      memory.save_assistant_message(final_answer)
      memory.save_qa_record(message, final_answer)
      memory.add_concern(message)
      memory.add_note(final_answer)
    except Exception as exc:
      logger.error('{"component":"chat_service","event":"MEMORY_PERSIST_FAILED","error":"%s"}', type(exc).__name__)

  explanation = None
  grounding_score: int | None = None
  if include_explanation and docs:
    explanation, grounding_score = state.explain_engine.build_explanation(message, docs, docs)

  return ChatResponse(
    answer=final_answer,
    safety_category=category,
    safety_guidance=safety_guidance,
    sources=_docs_to_sources(docs),
    explanation=explanation,
    grounding_score=grounding_score,
    detected_language=user_lang if ctx else None,
    patient_id=patient_id,
  )
