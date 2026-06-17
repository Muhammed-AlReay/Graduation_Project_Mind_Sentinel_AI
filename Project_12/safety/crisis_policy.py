"""
Centralized crisis policy engine.
All routes must use this module — no duplicated crisis/RAG gating logic.
"""
from typing import Literal, TypedDict

CrisisCategory = Literal["SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"]


class CrisisPolicyResult(TypedDict):
  category: CrisisCategory
  use_safety_response: bool
  use_crisis_protocol: bool
  allow_rag: bool
  skip_normal_rag: bool
  crisis_mode: bool


def apply_crisis_policy(category: str) -> CrisisPolicyResult:
  """
  Policy matrix:
    SUICIDE_RISK   → safety response, crisis protocol, NO normal RAG
    SELF_HARM      → safety response, crisis protocol, NO normal RAG
    CRISIS_DISTRESS → safety response, crisis protocol, RAG allowed
    SAFE           → normal RAG
  """
  normalized = category if category in (
    "SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"
  ) else "SAFE"

  is_crisis = normalized != "SAFE"
  skip_rag = normalized in ("SUICIDE_RISK", "SELF_HARM")
  allow_rag = normalized in ("SAFE", "CRISIS_DISTRESS")

  return CrisisPolicyResult(
    category=normalized,  # type: ignore[typeddict-item]
    use_safety_response=is_crisis,
    use_crisis_protocol=is_crisis,
    allow_rag=allow_rag,
    skip_normal_rag=skip_rag,
    crisis_mode=is_crisis,
  )
