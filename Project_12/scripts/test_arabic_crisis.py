#!/usr/bin/env python3
"""Validate Arabic crisis heuristic classification (no server/torch required)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from safety.heuristic_classifier import heuristic_crisis_classify

CASES = [
  # SUICIDE_RISK
  ("أشعر باليأس ولا أريد الاستمرار في الحياة", "SUICIDE_RISK"),
  ("لا أريد العيش بعد اليوم", "SUICIDE_RISK"),
  ("أفكر في الانتحار", "SUICIDE_RISK"),
  ("أريد أن أقتل نفسي", "SUICIDE_RISK"),
  ("لا فائدة من الحياة", "SUICIDE_RISK"),
  ("أريد أن أختفي ولن أعود", "SUICIDE_RISK"),
  ("لا سبب للعيش بعد الآن", "SUICIDE_RISK"),
  ("لا أريد أن أكمل الحياة", "SUICIDE_RISK"),
  # SELF_HARM
  ("أؤذي نفسي عندما أغضب", "SELF_HARM"),
  ("أفكر في إيذاء النفس", "SELF_HARM"),
  ("أجرح نفسي أحياناً", "SELF_HARM"),
  ("أضر نفسي عمداً", "SELF_HARM"),
  # CRISIS_DISTRESS
  ("أشعر باليأس ولا أرى أي أمل في المستقبل", "CRISIS_DISTRESS"),
  ("أنا يائس تماماً", "CRISIS_DISTRESS"),
  ("فقدت الأمل في كل شيء", "CRISIS_DISTRESS"),
  ("لا أستطيع الاستمرار هكذا", "CRISIS_DISTRESS"),
  ("لا أقدر على الاستمرار أكثر", "CRISIS_DISTRESS"),
  ("أشعر بانهيار نفسي", "CRISIS_DISTRESS"),
  ("بلا أمل من الغد", "CRISIS_DISTRESS"),
  ("حزين جداً ولا مخرج", "CRISIS_DISTRESS"),
  # SAFE
  ("أشعر بالقلق من العمل مؤخراً", "SAFE"),
  ("مرحباً، كيف حالك اليوم؟", "SAFE"),
  ("أريد نصيحة للنوم بشكل أفضل", "SAFE"),
  ("شكراً لمساعدتك", "SAFE"),
  ("أشعر بالتعب لكنني بخير", "SAFE"),
]


def main() -> int:
  passed = 0
  failed = []
  for text, expected in CASES:
    got = heuristic_crisis_classify(text)
    ok = got == expected
    if ok:
      passed += 1
    else:
      failed.append((text, expected, got))

  print(f"Arabic crisis heuristic: {passed}/{len(CASES)} passed")
  for text, expected, got in failed:
    print(f"  FAIL expected={expected} got={got} text={text!r}")

  return 0 if not failed else 1


if __name__ == "__main__":
  sys.exit(main())
