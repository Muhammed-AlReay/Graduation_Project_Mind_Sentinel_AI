"""Pydantic request/response models for the Project_12 API."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
  error: str
  detail: Optional[str] = None
  code: Optional[str] = None


class SourceDocument(BaseModel):
  content: str
  source: str = "Unknown"
  page: Optional[int | str] = None
  score: Optional[float] = None


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
  status: Literal["ok"] = "ok"
  service: str = "project12"
  version: str = "1.0.0"


class MetricsResponse(BaseModel):
  uptime_seconds: float
  request_count: int
  error_count: int
  rate_limit_count: int
  auth_failure_count: int


class ReadinessCheck(BaseModel):
  name: str
  ok: bool
  detail: Optional[str] = None


class ReadinessResponse(BaseModel):
  ready: bool
  checks: list[ReadinessCheck]


# ---------------------------------------------------------------------------
# POST /retrieve
# ---------------------------------------------------------------------------

class RetrieveRequest(BaseModel):
  query: str = Field(..., min_length=1, max_length=4000)
  top_k: Optional[int] = Field(None, ge=1, le=20)


class RetrieveResponse(BaseModel):
  query: str
  context: str
  sources: list[SourceDocument]
  chunk_count: int


# ---------------------------------------------------------------------------
# POST /crisis-detection
# ---------------------------------------------------------------------------

class CrisisDetectionRequest(BaseModel):
  text: str = Field(..., min_length=1, max_length=4000)


class CrisisDetectionResponse(BaseModel):
  category: Literal["SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"]
  safety_guidance: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /memory-search
# ---------------------------------------------------------------------------

class MemorySearchRequest(BaseModel):
  query: str = Field(..., min_length=1, max_length=1000)
  patient_id: Optional[str] = Field(None, max_length=64)
  max_results: int = Field(10, ge=1, le=50)


class MemoryMatch(BaseModel):
  patient_id: str
  match_type: Literal["concern", "note", "qa", "chat", "profile"]
  content: str
  metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchResponse(BaseModel):
  query: str
  matches: list[MemoryMatch]
  total: int


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
  role: Literal["user", "assistant"]
  content: str = Field(..., max_length=8000)


class ChatRequest(BaseModel):
  message: str = Field(..., min_length=1, max_length=4000)
  patient_id: Optional[str] = Field(None, max_length=64)
  chat_history: list[ChatMessage] = Field(default_factory=list, max_length=40)
  include_explanation: bool = False
  persist_memory: bool = True


class ChatResponse(BaseModel):
  answer: str
  safety_category: Literal["SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"]
  safety_guidance: Optional[str] = None
  sources: list[SourceDocument] = Field(default_factory=list)
  explanation: Optional[str] = None
  grounding_score: Optional[int] = None
  detected_language: Optional[str] = None
  patient_id: Optional[str] = None
