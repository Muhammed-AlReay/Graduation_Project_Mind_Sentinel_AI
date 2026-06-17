"""
Multilingual intent detection on ORIGINAL text (rule-based).
"""
from pipeline.language_detector import detect_language
from safety.heuristic_classifier import _matches_any

INTENT_PATTERNS = {
  "crisis_help": {
    "en": ["help me", "i need help", "emergency", "crisis", "can't cope"],
    "ar": ["ساعدني", "احتاج مساعدة", "طوارئ", "ازمة", "لا استطيع"],
    "fr": ["aidez-moi", "j'ai besoin d'aide", "urgence", "crise"],
    "es": ["ayúdame", "necesito ayuda", "emergencia", "crisis"],
    "it": ["aiutami", "ho bisogno di aiuto", "emergenza", "crisi"],
  },
  "information_seeking": {
    "en": ["what is", "tell me about", "explain", "how does", "symptoms of"],
    "ar": ["ما هو", "اخبرني عن", "اشرح", "كيف", "اعراض"],
    "fr": ["qu'est-ce que", "parlez-moi de", "expliquez", "symptômes"],
    "es": ["qué es", "cuéntame sobre", "explica", "síntomas"],
    "it": ["cos'è", "parlami di", "spiega", "sintomi"],
  },
  "emotional_venting": {
    "en": ["i feel", "i'm feeling", "i hate", "i can't", "so tired of"],
    "ar": ["اشعر", "أشعر", "اكره", "لا استطيع", "تعبت من"],
    "fr": ["je me sens", "je ressens", "je déteste", "je ne peux pas"],
    "es": ["me siento", "siento", "odio", "no puedo"],
    "it": ["mi sento", "sento", "odio", "non posso"],
  },
  "coping_request": {
    "en": ["how can i", "what should i do", "coping", "technique", "exercise"],
    "ar": ["كيف يمكنني", "ماذا افعل", "تأقلم", "تمرين", "تقنية"],
    "fr": ["comment puis-je", "que dois-je faire", "faire face"],
    "es": ["cómo puedo", "qué debo hacer", "afrontar"],
    "it": ["come posso", "cosa devo fare", "affrontare"],
  },
  "greeting": {
    "en": ["hello", "hi", "hey", "good morning", "good evening"],
    "ar": ["مرحبا", "اهلا", "السلام", "صباح", "مساء"],
    "fr": ["bonjour", "salut", "bonsoir"],
    "es": ["hola", "buenos días", "buenas tardes"],
    "it": ["ciao", "buongiorno", "buonasera"],
  },
}


def detect_intent(text: str) -> dict:
  lang = detect_language(text)
  best_intent = "general"
  best_score = 0

  for intent, lang_patterns in INTENT_PATTERNS.items():
    patterns = lang_patterns.get(lang, []) + lang_patterns.get("en", [])
    score = sum(
      1 for p in patterns
      if _matches_any(text, [p], arabic=(lang == "ar"))
    )
    if score > best_score:
      best_score = score
      best_intent = intent

  return {
    "intent": best_intent,
    "confidence": min(1.0, 0.25 + best_score * 0.25),
    "language": lang,
  }
