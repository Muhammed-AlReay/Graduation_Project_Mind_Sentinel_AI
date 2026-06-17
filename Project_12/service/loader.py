"""Singleton loader for models, vectorstore, and retrieval pipeline."""
import logging
import threading
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL, LLM_TIMEOUT_SECONDS, RETRIEVAL_CANDIDATE_K, VECTORSTORE_DIR
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from safety.crisis_handler import CrisisHandler
from safety.safety_guard import SafetyGuard
from service.startup import StartupReport, run_startup_validation
from utils.explainability import ExplainabilityEngine

logger = logging.getLogger(__name__)


class ServiceState:
  """Thread-safe lazy loader for all inference dependencies."""

  def __init__(self) -> None:
    self._lock = threading.RLock()
    self._embeddings: Optional[HuggingFaceEmbeddings] = None
    self._vectorstore: Optional[FAISS] = None
    self._docs: list = []
    self._hybrid_retriever: Optional[HybridRetriever] = None
    self._reranker: Optional[Reranker] = None
    self._llm = None
    self._safety_guard: Optional[SafetyGuard] = None
    self._crisis_handler: Optional[CrisisHandler] = None
    self._explain_engine: Optional[ExplainabilityEngine] = None
    self._startup_report: Optional[StartupReport] = None
    self._retrieval_ready = False
    self._llm_ready = False
    self._load_error: Optional[str] = None

  @property
  def llm_timeout(self) -> int:
    return LLM_TIMEOUT_SECONDS

  def initialize(self) -> StartupReport:
    with self._lock:
      if self._startup_report is not None:
        return self._startup_report

      logger.info("Running startup validation")
      self._startup_report = run_startup_validation()

      vectorstore_check = next(
        (c for c in self._startup_report.checks if c.name in ("vectorstore_files", "vectorstore_build")),
        None,
      )
      if vectorstore_check and vectorstore_check.ok:
        try:
          self._load_retrieval_stack()
          self._retrieval_ready = True
          logger.info("Retrieval stack loaded successfully")
        except Exception as exc:
          self._load_error = str(exc)
          logger.exception("Failed to load retrieval stack")

      api_check = next(
        (c for c in self._startup_report.checks if c.name == "openrouter_api_key"),
        None,
      )
      if api_check and api_check.ok:
        try:
          self._load_llm_stack()
          self._llm_ready = True
          logger.info("LLM stack loaded successfully")
        except Exception as exc:
          self._load_error = self._load_error or str(exc)
          logger.exception("Failed to load LLM stack")

      return self._startup_report

  def _load_retrieval_stack(self) -> None:
    if self._vectorstore is not None:
      return

    logger.info("Loading embeddings model: %s", EMBEDDING_MODEL)
    self._embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    logger.info("Loading FAISS vectorstore from %s", VECTORSTORE_DIR)
    self._vectorstore = FAISS.load_local(
      str(VECTORSTORE_DIR),
      self._embeddings,
      allow_dangerous_deserialization=True,
    )
    self._docs = list(self._vectorstore.docstore._dict.values())
    self._hybrid_retriever = HybridRetriever(self._vectorstore, self._docs)
    self._reranker = Reranker()
    self._explain_engine = ExplainabilityEngine()

  def _load_llm_stack(self) -> None:
    if self._llm is not None:
      return

    from llm_router import get_llm

    logger.info("Initializing LLM")
    self._llm = get_llm()
    self._safety_guard = SafetyGuard(self._llm)
    self._crisis_handler = CrisisHandler()

  @property
  def retrieval_ready(self) -> bool:
    return self._retrieval_ready

  @property
  def llm_ready(self) -> bool:
    return self._llm_ready

  @property
  def ready(self) -> bool:
    return self._retrieval_ready and self._llm_ready

  @property
  def load_error(self) -> Optional[str]:
    return self._load_error

  def require_retrieval(self) -> None:
    if not self._retrieval_ready:
      raise RuntimeError(self._load_error or "Retrieval stack not loaded")

  def require_llm(self) -> None:
    if not self._llm_ready:
      raise RuntimeError(self._load_error or "LLM stack not loaded")

  @property
  def hybrid_retriever(self) -> HybridRetriever:
    self.require_retrieval()
    assert self._hybrid_retriever is not None
    return self._hybrid_retriever

  @property
  def reranker(self) -> Reranker:
    self.require_retrieval()
    assert self._reranker is not None
    return self._reranker

  @property
  def safety_guard(self) -> SafetyGuard:
    self.require_llm()
    assert self._safety_guard is not None
    return self._safety_guard

  @property
  def crisis_handler(self) -> CrisisHandler:
    self.require_llm()
    assert self._crisis_handler is not None
    return self._crisis_handler

  @property
  def llm(self):
    self.require_llm()
    return self._llm

  @property
  def explain_engine(self) -> ExplainabilityEngine:
    self.require_retrieval()
    assert self._explain_engine is not None
    return self._explain_engine


state = ServiceState()
