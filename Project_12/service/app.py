"""FastAPI application for Project_12 production service."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import RETRIEVAL_TOP_K, SERVICE_HOST, SERVICE_PORT
from service.chat_service import process_chat
from service.loader import state
from service.logging_config import setup_logging
from service.memory_search import search_memory
from service.metrics import metrics
from service.models import (
  ChatRequest,
  ChatResponse,
  CrisisDetectionRequest,
  CrisisDetectionResponse,
  ErrorResponse,
  HealthResponse,
  MemorySearchRequest,
  MemorySearchResponse,
  MetricsResponse,
  ReadinessCheck,
  ReadinessResponse,
  RetrieveRequest,
  RetrieveResponse,
  SourceDocument,
)
from service.security.middleware import SecurityMiddleware
from service.startup import run_startup_validation

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("Project_12 service starting up")
  report = state.initialize()
  for check in report.checks:
    level = logging.INFO if check.ok else logging.WARNING
    logger.log(level, "Startup check [%s]: ok=%s detail=%s", check.name, check.ok, check.detail)
  yield
  logger.info("Project_12 service shutting down")


app = FastAPI(
  title="Project_12 AI Service",
  description="Production RAG mental health intelligence layer",
  version="1.1.0",
  lifespan=lifespan,
)

app.add_middleware(SecurityMiddleware)


def _error_response(status_code: int, error: str, code: str, detail: str) -> JSONResponse:
  return JSONResponse(
    status_code=status_code,
    content=ErrorResponse(error=error, detail=detail, code=code).model_dump(),
  )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
  return _error_response(
    status.HTTP_422_UNPROCESSABLE_ENTITY,
    "validation_error",
    "VALIDATION_ERROR",
    "Request validation failed",
  )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
  if exc.status_code == 400:
    return _error_response(400, "bad_request", "BAD_REQUEST", "Malformed request")
  raise exc


@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request: Request, exc: RuntimeError):
  logger.error("Runtime error on %s: %s", request.url.path, exc)
  return _error_response(
    status.HTTP_503_SERVICE_UNAVAILABLE,
    "service_unavailable",
    "SERVICE_UNAVAILABLE",
    str(exc),
  )


@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
  logger.warning("Timeout on %s: %s", request.url.path, exc)
  return _error_response(
    status.HTTP_504_GATEWAY_TIMEOUT,
    "timeout",
    "TIMEOUT",
    str(exc),
  )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
  logger.exception("Unhandled error on %s", request.url.path)
  return _error_response(
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    "internal_error",
    "INTERNAL_ERROR",
    "An unexpected error occurred",
  )


# ---------------------------------------------------------------------------
# Monitoring endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["monitoring"])
async def health():
  """Liveness probe — process is running. No auth required."""
  return HealthResponse()


@app.get("/ready", response_model=ReadinessResponse, tags=["monitoring"])
async def ready():
  """Readiness probe — models and vectorstore are loaded. No auth required."""
  report = state._startup_report or run_startup_validation()
  checks = [
    ReadinessCheck(name=c.name, ok=c.ok, detail=c.detail)
    for c in report.checks
  ]
  checks.append(
    ReadinessCheck(
      name="retrieval_stack",
      ok=state.retrieval_ready,
      detail=state.load_error if not state.retrieval_ready else "Loaded",
    )
  )
  checks.append(
    ReadinessCheck(
      name="llm_stack",
      ok=state.llm_ready,
      detail=state.load_error if not state.llm_ready else "Loaded",
    )
  )
  is_ready = state.ready and report.ready
  return ReadinessResponse(ready=is_ready, checks=checks)


@app.get("/metrics", response_model=MetricsResponse, tags=["monitoring"])
async def get_metrics():
  """Operational metrics — requires API key authentication."""
  snap = metrics.snapshot()
  return MetricsResponse(
    uptime_seconds=snap.uptime_seconds,
    request_count=snap.request_count,
    error_count=snap.error_count,
    rate_limit_count=snap.rate_limit_count,
    auth_failure_count=snap.auth_failure_count,
  )


# ---------------------------------------------------------------------------
# Inference endpoints (all require API key)
# ---------------------------------------------------------------------------

@app.post("/retrieve", response_model=RetrieveResponse, tags=["inference"])
async def retrieve(body: RetrieveRequest):
  """Hybrid BM25 + FAISS retrieval with cross-encoder reranking."""
  state.require_retrieval()
  top_k = body.top_k or RETRIEVAL_TOP_K

  docs = state.hybrid_retriever.get_relevant_documents(body.query)
  docs = state.reranker.rerank(body.query, docs, top_k=top_k)

  sources = [
    SourceDocument(
      content=doc.page_content,
      source=str(doc.metadata.get("source", "Unknown")).split("/")[-1].split("\\")[-1],
      page=doc.metadata.get("page"),
    )
    for doc in docs
  ]
  context = "\n\n".join(doc.page_content for doc in docs)

  return RetrieveResponse(
    query=body.query,
    context=context,
    sources=sources,
    chunk_count=len(docs),
  )


@app.post("/crisis-detection", response_model=CrisisDetectionResponse, tags=["inference"])
async def crisis_detection(body: CrisisDetectionRequest):
  """LLM-based safety classification with heuristic fallback on provider failure."""
  from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

  from safety.heuristic_classifier import heuristic_crisis_classify

  state.require_llm()
  category = "SAFE"
  used_fallback = False

  def classify():
    return state.safety_guard.classify(body.text)

  try:
    with ThreadPoolExecutor(max_workers=1) as pool:
      future = pool.submit(classify)
      try:
        category = future.result(timeout=state.llm_timeout)
      except FuturesTimeoutError:
        logger.warning(
          '{"component":"crisis-detection","event":"timeout","fallback":"heuristic"}'
        )
        category = heuristic_crisis_classify(body.text)
        used_fallback = True
  except Exception as exc:
    logger.exception(
      '{"component":"crisis-detection","event":"unexpected_error","error_type":"%s"}',
      type(exc).__name__,
    )
    category = heuristic_crisis_classify(body.text)
    used_fallback = True

  if category not in ("SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"):
    logger.warning(
      '{"component":"crisis-detection","event":"invalid_category","fallback":"heuristic"}'
    )
    category = heuristic_crisis_classify(body.text)
    used_fallback = True

  if category == "SUICIDE_RISK":
    logger.info('{"component":"crisis-detection","event":"SUICIDE_DETECTED","used_fallback":%s}', str(used_fallback).lower())
  elif category == "SELF_HARM":
    logger.info('{"component":"crisis-detection","event":"SELF_HARM_DETECTED","used_fallback":%s}', str(used_fallback).lower())
  elif category != "SAFE":
    logger.info('{"component":"crisis-detection","event":"CRISIS_PIPELINE_ACTIVATED","category":"%s","used_fallback":%s}', category, str(used_fallback).lower())
  else:
    logger.info(
      '{"component":"crisis-detection","event":"classified","category":"SAFE","used_fallback":%s}',
      str(used_fallback).lower(),
    )

  safety_guidance = None
  if category != "SAFE":
    safety_guidance = state.crisis_handler.get_response(category, body.text)

  return CrisisDetectionResponse(category=category, safety_guidance=safety_guidance)


@app.post("/memory-search", response_model=MemorySearchResponse, tags=["inference"])
async def memory_search(body: MemorySearchRequest):
  """Search patient memory stores (concerns, notes, QA logs, chats)."""
  matches = search_memory(
    query=body.query,
    patient_id=body.patient_id,
    max_results=body.max_results,
  )
  return MemorySearchResponse(query=body.query, matches=matches, total=len(matches))


@app.post("/chat", response_model=ChatResponse, tags=["inference"])
async def chat(body: ChatRequest):
  """Full RAG chat with safety classification and optional memory persistence."""
  import time
  state.require_retrieval()
  state.require_llm()

  # [PROOF-LOGGING B.5] — temporary, for runtime verification only
  t_start = time.time()
  logger.info(
    '[PROJECT12_GENERATION_USED] /chat received msg_len=%d history_len=%d ts=%.3f',
    len(body.message), len(body.chat_history), t_start,
  )

  result = process_chat(
    state=state,
    message=body.message,
    patient_id=body.patient_id,
    chat_history=body.chat_history,
    include_explanation=body.include_explanation,
    persist_memory=body.persist_memory,
  )

  # [PROOF-LOGGING B.5]
  logger.info(
    '[PROJECT12_GENERATION_USED] /chat answered safety=%s answer_len=%d elapsed_ms=%d',
    result.safety_category, len(result.answer), int((time.time() - t_start) * 1000),
  )
  return result


def main():
  import uvicorn

  uvicorn.run(
    "service.app:app",
    host=SERVICE_HOST,
    port=SERVICE_PORT,
    log_level="info",
  )


if __name__ == "__main__":
  main()