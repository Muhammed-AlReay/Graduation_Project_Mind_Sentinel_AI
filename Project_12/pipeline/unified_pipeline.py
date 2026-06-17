"""
Unified multilingual AI pipeline.

Flow:
  User Input (original language)
    → Safety Layer (original)
    → Crisis Detection (original)
    → Emotion Detection (original)
    → Intent Detection (original)
    → Language Detection
    → Translation → Canonical English
    → RAG (if policy allows)
    → Memory
    → Project_12 LLM
    → Translation back
    → User language
"""
import logging
from dataclasses import dataclass, field

from pipeline.emotion_detector import detect_emotion
from pipeline.intent_detector import detect_intent
from pipeline.language_detector import detect_language
from pipeline.translation import TranslationLayer
from safety.crisis_policy import apply_crisis_policy

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
  original_text: str
  detected_language: str
  canonical_english: str
  safety_category: str
  crisis_policy: dict
  emotion: dict
  intent: dict
  used_translation: bool = False
  metadata: dict = field(default_factory=dict)


def run_pre_translation_analysis(text: str, safety_guard) -> tuple[str, dict, dict, dict]:
  """
  All safety/crisis/emotion/intent on ORIGINAL text before any translation.
  """
  category = safety_guard.classify(text)
  policy = apply_crisis_policy(category)
  emotion = detect_emotion(text)
  intent = detect_intent(text)
  return category, policy, emotion, intent


def build_pipeline_context(
  text: str,
  safety_guard,
  translator: TranslationLayer | None = None,
) -> PipelineContext:
  lang = detect_language(text)
  category, policy, emotion, intent = run_pre_translation_analysis(text, safety_guard)

  canonical = text
  used_translation = False
  if translator and lang != "en":
    canonical, lang = translator.to_canonical_english(text, lang)
    used_translation = canonical != text

  logger.info(
    '{"component":"unified_pipeline","event":"context_built",'
    '"lang":"%s","category":"%s","intent":"%s","emotion":"%s","translated":%s}',
    lang, category, intent.get("intent"), emotion.get("emotion"), str(used_translation).lower(),
  )

  return PipelineContext(
    original_text=text,
    detected_language=lang,
    canonical_english=canonical,
    safety_category=category,
    crisis_policy=policy,
    emotion=emotion,
    intent=intent,
    used_translation=used_translation,
  )
