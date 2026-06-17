"""
Script-based language detection for supported UI languages.
"""
import re

SUPPORTED_LANGUAGES = ("en", "ar", "fr", "es", "it")

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_LATIN_RE = re.compile(r"[a-zA-ZÀ-ÿ]")
_FRENCH_MARKERS = re.compile(
  r"\b(je|tu|vous|nous|est|sont|pas|une|des|avec|pour|très|être|avoir|suicid)\b", re.I
)
_SPANISH_MARKERS = re.compile(
  r"\b(yo|tú|usted|nosotros|es|son|no|una|con|para|muy|estar|tener|suicid)\b", re.I
)
_ITALIAN_MARKERS = re.compile(
  r"\b(io|tu|lei|noi|è|sono|non|una|con|per|molto|essere|avere|suicid)\b", re.I
)


def detect_language(text: str) -> str:
  if not text or not text.strip():
    return "en"

  ar_count = len(_ARABIC_RE.findall(text))
  latin_count = len(_LATIN_RE.findall(text))

  if ar_count > latin_count and ar_count > 0:
    return "ar"

  lower = text.lower()
  fr = len(_FRENCH_MARKERS.findall(lower))
  es = len(_SPANISH_MARKERS.findall(lower))
  it = len(_ITALIAN_MARKERS.findall(lower))

  if fr >= es and fr >= it and fr >= 2:
    return "fr"
  if es >= fr and es >= it and es >= 2:
    return "es"
  if it >= fr and it >= es and it >= 2:
    return "it"

  return "en"
