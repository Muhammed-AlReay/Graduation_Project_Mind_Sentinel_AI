import logging

from langchain_core.prompts import ChatPromptTemplate

from safety.heuristic_classifier import heuristic_crisis_classify

logger = logging.getLogger(__name__)


class SafetyGuard:

    def __init__(self, llm):
        self.llm = llm

        self.classifier_prompt = ChatPromptTemplate.from_messages([
            ("system",
             """
You are a mental health safety classifier.

Classify the user message into ONE category only:

Categories:
- SAFE
- SUICIDE_RISK
- SELF_HARM
- CRISIS_DISTRESS

Rules:
- If user talks about death, suicide, not wanting to live, wanting to disappear, no reason to live → SUICIDE_RISK
- If user talks about harming themselves → SELF_HARM
- If extreme panic, hopelessness, despair, breakdown → CRISIS_DISTRESS
- Otherwise → SAFE

Arabic examples (classify by meaning, not language):
- "أشعر باليأس ولا أرى أي أمل" → CRISIS_DISTRESS
- "لا أريد العيش بعد اليوم" → SUICIDE_RISK
- "أريد أن أختفي ولن أستطيع الاستمرار" → SUICIDE_RISK
- "أؤذي نفسي عندما أغضب" → SELF_HARM

Return ONLY the label. No explanation.
"""),
            ("human", "{input}")
        ])

        self.chain = self.classifier_prompt | self.llm

    def _normalize_llm_label(self, raw: str) -> str:
        category = raw.strip().upper()

        if "SUICIDE" in category:
            return "SUICIDE_RISK"

        if "SELF_HARM" in category or "SELF HARM" in category:
            return "SELF_HARM"

        if "CRISIS" in category:
            return "CRISIS_DISTRESS"

        if category in ("SAFE", "SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"):
            return category

        return "SAFE"

    def _extract_content(self, result) -> str | None:
        content = getattr(result, "content", None)
        if content is None:
            return None
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return " ".join(parts) if parts else None
        return str(content)

    def classify(self, text: str) -> str:
        # Fast EN/AR heuristic for high-signal crisis language (also used when LLM blocks).
        heuristic = heuristic_crisis_classify(text)
        if heuristic != "SAFE":
            if heuristic == "SUICIDE_RISK":
                logger.info('{"component":"SafetyGuard","event":"SUICIDE_DETECTED","source":"heuristic"}')
            elif heuristic == "SELF_HARM":
                logger.info('{"component":"SafetyGuard","event":"SELF_HARM_DETECTED","source":"heuristic"}')
            else:
                logger.info('{"component":"SafetyGuard","event":"CRISIS_PIPELINE_ACTIVATED","category":"%s","source":"heuristic"}', heuristic)
            return heuristic

        try:
            result = self.chain.invoke({"input": text})
            content = self._extract_content(result)

            if not content or not content.strip():
                logger.warning(
                    '{"component":"SafetyGuard","event":"empty_llm_response","fallback":"heuristic"}'
                )
                return heuristic_crisis_classify(text)

            return self._normalize_llm_label(content)

        except Exception as exc:
            exc_type = type(exc).__name__
            # OpenRouter free-tier moderation returns 403 when crisis language is present.
            is_moderation = "403" in str(exc) or "PermissionDenied" in exc_type
            logger.warning(
                '{"component":"SafetyGuard","event":"llm_classify_failed",'
                '"error_type":"%s","moderation_block":%s,"fallback":"heuristic"}',
                exc_type,
                str(is_moderation).lower(),
            )
            return heuristic_crisis_classify(text)
