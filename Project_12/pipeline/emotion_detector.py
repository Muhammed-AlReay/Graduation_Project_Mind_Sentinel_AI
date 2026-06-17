"""
Multilingual emotion detection on ORIGINAL text (rule-based, no LLM).
Supporting signal only — not a diagnosis.
"""
import re

from pipeline.language_detector import detect_language
from safety.heuristic_classifier import _matches_any, _normalize_arabic

EMOTION_KEYWORDS = {
  "calm": {
    "en": ["peaceful", "relaxed", "content", "okay", "fine", "good", "happy", "great"],
    "ar": ["هادئ", "مسترخي", "بخير", "سعيد", "مرتاح"],
    "fr": ["paisible", "détendu", "content", "bien", "heureux"],
    "es": ["tranquilo", "relajado", "contento", "bien", "feliz"],
    "it": ["tranquillo", "rilassato", "contento", "bene", "felice"],
  },
  "mild_stress": {
    "en": ["worried", "concerned", "nervous", "uneasy", "tense", "pressure", "busy", "tired"],
    "ar": ["قلق", "متوتر", "ضغط", "متعب", "مشغول"],
    "fr": ["inquiet", "nerveux", "tendu", "fatigué", "stressé"],
    "es": ["preocupado", "nervioso", "tenso", "cansado", "estresado"],
    "it": ["preoccupato", "nervoso", "teso", "stanco", "stressato"],
  },
  "moderate_anxiety": {
    "en": ["anxious", "panic", "fear", "scared", "overwhelmed", "racing", "restless", "dread"],
    "ar": ["خائف", "فزع", "ذعر", "مذعور", "قلق شديد", "مضطرب"],
    "fr": ["anxieux", "panique", "peur", "effrayé", "débordé"],
    "es": ["ansioso", "pánico", "miedo", "asustado", "abrumado"],
    "it": ["ansioso", "panico", "paura", "spaventato", "sopraffatto"],
  },
  "severe_depression": {
    "en": ["hopeless", "worthless", "empty", "numb", "dark", "nothing matters", "give up", "alone"],
    "ar": ["يائس", "بلا امل", "فارغ", "وحيد", "حزين", "مكتئب", "اكتئاب"],
    "fr": ["désespéré", "sans espoir", "vide", "seul", "triste", "déprimé"],
    "es": ["desesperado", "sin esperanza", "vacío", "solo", "triste", "deprimido"],
    "it": ["disperato", "senza speranza", "vuoto", "solo", "triste", "depresso"],
  },
  "burnout": {
    "en": ["exhausted", "burned out", "drained", "depleted", "overworked", "no energy"],
    "ar": ["منهك", "محترق", "لا طاقة", "مرهق", "تعبت"],
    "fr": ["épuisé", "burn-out", "vidé", "sans énergie"],
    "es": ["agotado", "quemado", "sin energía", "agotamiento"],
    "it": ["esausto", "burnout", "senza energia", "esaurito"],
  },
}

INTENSITY_MAP = {
  "calm": 0.2,
  "mild_stress": 0.4,
  "moderate_anxiety": 0.65,
  "severe_depression": 0.9,
  "burnout": 0.8,
}


def _score_keywords(text: str, keywords: list[str], lang: str) -> int:
  if lang == "ar":
    return sum(1 for k in keywords if _matches_any(text, [k], arabic=True))
  lower = text.lower()
  return sum(1 for k in keywords if k.lower() in lower)


def detect_emotion(text: str) -> dict:
  lang = detect_language(text)
  best_emotion = "calm"
  best_score = 0

  for emotion, lang_keywords in EMOTION_KEYWORDS.items():
    keywords = lang_keywords.get(lang, []) + lang_keywords.get("en", [])
    score = _score_keywords(text, keywords, lang)
    if score > best_score:
      best_score = score
      best_emotion = emotion

  return {
    "emotion": best_emotion,
    "intensity": INTENSITY_MAP.get(best_emotion, 0.3),
    "confidence": min(1.0, 0.3 + best_score * 0.2),
    "language": lang,
  }
