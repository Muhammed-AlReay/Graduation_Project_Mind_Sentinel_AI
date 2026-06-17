"""
Internal translation layer — preserves safety/crisis/emotional/medical meaning.
Classification always runs on original text BEFORE translation.
"""
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from pipeline.language_detector import SUPPORTED_LANGUAGES, detect_language

logger = logging.getLogger(__name__)

_TRANSLATE_TO_EN_PROMPT = ChatPromptTemplate.from_messages([
  ("system",
   """You are a precise medical-psychology translator.
Translate the user message to English.
Preserve: safety meaning, crisis signals, emotional tone, medical terms.
Return ONLY the English translation — no commentary."""),
  ("human", "Source language: {lang}\n\n{text}"),
])

_TRANSLATE_FROM_EN_PROMPT = ChatPromptTemplate.from_messages([
  ("system",
   """You are a precise medical-psychology translator.
Translate the assistant response from English to {target_lang}.
Preserve: safety meaning, crisis guidance, emotional warmth, medical accuracy.
Use natural, culturally appropriate phrasing.
Return ONLY the translated response — no commentary."""),
  ("human", "{text}"),
])


def _extract_content(result) -> str:
  content = getattr(result, "content", None)
  if isinstance(content, str):
    return content.strip()
  if isinstance(content, list):
    parts = []
    for block in content:
      if isinstance(block, str):
        parts.append(block)
      elif isinstance(block, dict) and block.get("type") == "text":
        parts.append(str(block.get("text", "")))
    return " ".join(parts).strip()
  return str(content or "").strip()


class TranslationLayer:
  def __init__(self, llm):
    self.llm = llm
    self._to_en = _TRANSLATE_TO_EN_PROMPT | llm
    self._from_en = _TRANSLATE_FROM_EN_PROMPT | llm

  def to_canonical_english(self, text: str, source_lang: str | None = None) -> tuple[str, str]:
    """Returns (canonical_english, detected_lang)."""
    lang = source_lang or detect_language(text)
    if lang == "en":
      return text, lang
    try:
      result = self._to_en.invoke({"lang": lang, "text": text})
      translated = _extract_content(result)
      if translated:
        return translated, lang
    except Exception as exc:
      logger.warning(
        '{"component":"translation","event":"to_en_failed","lang":"%s","error":"%s"}',
        lang, type(exc).__name__,
      )
    return text, lang

  def from_english(self, text: str, target_lang: str) -> str:
    if target_lang == "en" or not text.strip():
      return text
    if target_lang not in SUPPORTED_LANGUAGES:
      return text
    try:
      result = self._from_en.invoke({"target_lang": target_lang, "text": text})
      translated = _extract_content(result)
      if translated:
        return translated
    except Exception as exc:
      logger.warning(
        '{"component":"translation","event":"from_en_failed","lang":"%s","error":"%s"}',
        target_lang, type(exc).__name__,
      )
    return text
