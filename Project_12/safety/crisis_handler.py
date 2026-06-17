import re


def _is_arabic(text: str) -> bool:
  if not text:
    return False
  ar = len(re.findall(r"[\u0600-\u06FF]", text))
  en = len(re.findall(r"[a-zA-Z]", text))
  return ar >= en and ar > 0


class CrisisHandler:

    def get_response(self, category: str, user_text: str = ""):
        ar = _is_arabic(user_text)

        if category == "SUICIDE_RISK":
            if ar:
                return (
                    "أنا آسف أنك تمر بهذا الوقت الصعب 💔\n\n"
                    "أنا هنا معك، لكن الأهم الآن أن تتواصل مع شخص قريب منك أو مختص فوراً.\n\n"
                    "إذا كان هناك خطر فوري، اتصل بخدمات الطوارئ في بلدك (مثال مصر: 16328).\n\n"
                    "من المهم جداً ألا تبقى وحيداً في هذه اللحظة."
                )
            return (
                "I'm sorry you're going through a difficult time 💔\n\n"
                "I'm here with you, but the most important thing is that you contact someone close to you or a professional immediately.\n\n"
                "If there is immediate danger, please contact the emergency services in your country.\n\n"
                "It's very important that you're not alone at this moment."
            )

        if category == "SELF_HARM":
            if ar:
                return (
                    "أنا قلق عليك ❤️\n\n"
                    "إيذاء النفس ليس الحل، وهناك دعم حقيقي يمكنه مساعدتك في تجاوز هذه اللحظة.\n"
                    "حاول التحدث مع شخص تثق به أو مع مختص في الصحة النفسية."
                )
            return (
                "I'm worried about you ❤️\n\n"
                "Harming yourself isn't the answer, and there's real support that can help you get through this moment.\n"
                "Try talking to someone you trust or a mental health professional."
            )

        if category == "CRISIS_DISTRESS":
            if ar:
                return (
                    "يبدو أنك تحت ضغط كبير 😔\n\n"
                    "لنأخذ خطوة بسيطة: تنفس بعمق وحاول أن تهدأ قليلاً.\n"
                    "إذا استطعت، حاول التحدث مع شخص قريب منك."
                )
            return (
                "It's clear you're under a lot of pressure 😔\n\n"
                "Let's take a simple step: take a deep breath and calm down a bit.\n"
                "If you can, try talking to someone close to you."
            )

        if ar:
            return "أنا هنا لمساعدتك. هل يمكنك أن تخبرني أكثر عما تشعر به؟"
        return "I'm here to help. Could you tell me a little more about what you're experiencing?"
