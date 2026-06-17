"""
Keyword heuristic crisis classifier — fallback when LLM provider blocks or fails.
Used by SafetyGuard when OpenRouter moderation rejects crisis-language inputs.
Supports English and Arabic phrase matching (including Egyptian dialect).
"""
import re
import unicodedata


def _normalize_arabic(text: str) -> str:
  """Strip diacritics and normalize alef/yaa/taa marbuta variants for matching."""
  text = unicodedata.normalize("NFKC", text)
  text = re.sub(r"[\u064B-\u065F\u0670]", "", text)  # tashkeel
  text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
  text = text.replace("ى", "ي").replace("ة", "ه")
  return text


def _matches_any(text: str, patterns: list[str], *, arabic: bool = False) -> bool:
  haystack = _normalize_arabic(text) if arabic else text.lower()
  for pattern in patterns:
    needle = _normalize_arabic(pattern) if arabic else pattern.lower()
    if needle in haystack:
      return True
  return False

# English patterns (Massively Expanded)
SUICIDE_PATTERNS_EN = [
    "suicide", "kill myself", "end it all", "want to die", "no reason to live",
    "better off dead", "end my life", "don't want to live", "do not want to live",
    "don't want to continue living", "do not want to continue living",
    "not want to continue living", "take my life", "want to disappear",
    "cannot continue living", "can't continue living", "i want to die", "wish i was dead",
    "thinking about suicide", "thinking of killing myself",
    "i want to end my life", "i don't want to be alive",
    "life is not worth living", "everyone would be better without me",
    "i want to disappear forever", "i cannot do this anymore",
    "i wish i could sleep and never wake up", "there is nothing left for me",
    "i have no reason to keep going", "commit suicide",
    "going to end my life", "don't want to live anymore", "do not want to live anymore",
    "want to end my life", "going to kill myself", "let me die", "hope i die",
    "i will be dead", "died in", "die right now", "me to kill", "kill themselves",
    "kill herself", "killing people", "would kill", "deserve to die", "to die in",
    "ending his life", "ended his life", "ends his life", "ending her life",
    "ended her life", "ends her life", "ending own life", "ended own life",
    "ends own life", "killing herself", "killed herself", "kill herself",
    "kills herself", "killing yourself", "killed yourself", "kill yourself",
    "kills yourself", "killing myself", "killed myself", "kill myself",
    "kills myself", "killing hisself", "killed hisself", "kill hisself",
    "kills hisself", "take her life", "takes her life", "took her life",
    "taking her life", "take your life", "takes your life", "took your life",
    "taking your life", "take my life", "takes my life", "took my life",
    "taking my life", "take his life", "takes his life", "took his life",
    "taking his life", "take own life", "takes own life", "took own life",
    "taking own life", "end her life", "ending her life", "ended her life",
    "ends her life", "end your life", "ending your life", "ended your life",
    "ends your life", "end my life", "ending my life", "ended my life",
    "ends my life", "end his life", "ending his life", "ended his life",
    "ends his life", "want to die", "wants to die", "wanting to die",
    "wanted to die", "want to end life", "wants to end life", "wanting to end life",
    "wanted to end life", "suicidal", "suicidal ideation", "suicidality",
    "suicidal behaviors", "suicidal thoughts", "suicidal ideas", "si",
    "wish to die", "wish to be dead", "better off dead", "want to die",
    "life not worth living", "thoughts of suicide", "hanging myself", "overdosing",
    "jump off", "bridge", "goodbye world", "final letter", "final goodbye",
    "can't take the pain", "pain is too much", "ready to go", "not coming back",
    "see you in the next life", "peace out forever", "no more suffering"
]

SELF_HARM_PATTERNS_EN = [
    "self harm", "self-harm", "hurt myself", "cut myself", "harm myself",
    "burn myself", "scratch myself", "injure myself", "punish myself",
    "blade", "wrists", "harm", "days clean", "scars", "stains", "cuts",
    "purged", "cals", "i cut", "cutting", "needle", "my weight", "i need to cut",
    "marks", "bleed", "my wrist", "do not cut", "flesh", "self-care",
    "barcode", "zebra crossing", "cat scratched me", "secret society 123",
    "slice", "burning myself", "hitting myself", "banging head", "blood",
    "relapsed", "weeks clean", "months clean", "staying clean", "razor",
    "sharps", "bandages", "hiding scars", "long sleeves", "covering up"
]

DISTRESS_PATTERNS_EN = [
    "hopeless", "worthless", "can't go on", "cant go on", "breakdown",
    "overwhelmed", "no way out", "give up on life", "extremely stressed",
    "losing control", "panic attack", "i feel trapped", "i feel broken",
    "emotionally exhausted", "coping", "do not deserve to", "social anxie",
    "mental disease", "mentally ill", "mental health", "adhd", "dysthymia",
    "ocd", "ptsd", "ptsr", "ptss", "schizo", "depres", "mdd", "anxiety",
    "trauma", "cishet", "dehumanizing", "so angry", "i dont want to",
    "controlled", "ableist", "counselling", "disorder", "i will never be",
    "voices in my", "want to hug", "dysphoria", "hear voices", "celexa",
    "illness", "getting worse", "they do not care", "im screaming", "ranting",
    "run away", "nausea", "borderline", "citalopram", "insecure", "unbearable",
    "diseases", "sorry for being", "i am sorry that", "sexually", "horrid",
    "i give up", "relapsing", "need to talk", "emo", "thinspo", "grieving",
    "feel sick", "getting bad again", "deal with it", "i am so sick", "bothered",
    "prescribed", "admitted", "abusive", "dizzy", "puking", "a victim",
    "really sad", "weeks clean", "my existence", "trigger", "manic",
    "mental hospital", "irl friends", "survivor", "hearing voices",
    "wanting to die", "i am scared", "want to help", "afraid that", "tense",
    "masturbating", "not alone", "the voices in", "have to deal with", "effexor",
    "gives a shit", "do not want to eat", "offend", "was forced", "alcoholism",
    "feel like shit", "actually crying", "months clean", "shit like this",
    "tendencies", "horrifying", "useless", "to hurt myself", "vile", "recover",
    "wellbutrin", "guilt", "razor", "hate everything", "horny", "duloxetine",
    "counsellor", "feel the same way", "paranoid", "hallucinating", "free will",
    "weight loss", "sexuality", "syndrome", "destructive", "cannibal", "damage",
    "sorry to hear that", "it hurts so much", "problematic", "hope you are ok",
    "hope you are well", "disappear", "unstable", "manipulating", "underweight",
    "insulted", "treatment", "vaginas", "i would feel", "helped me a lot",
    "no one likes me", "injection", "my mental", "sorrow", "isolated", "drained",
    "what i am going", "esteem", "rough day", "misogynist", "threatening",
    "not available", "kill him", "shrink", "voices are", "i have not spoken to",
    "vulnerable", "collarbones", "hallucinations", "i have lost", "i can not bring myself",
    "healing", "psych", "nostalgic", "i need to lose", "rapist", "cries", "the feels",
    "purging", "that feel when", "toxic", "overwhelming", "hurtful", "doxycycline",
    "sad all the time", "empathy", "insomnia", "vent", "grave", "seroquel",
    "to live anymore", "endure", "i have been feeling", "distress", "restless",
    "the bottom of the", "consent", "overdose", "lethal", "stabbed", "talentless",
    "punish", "relapse", "save me from myself", "rest of my life", "near the end of",
    "a burden", "for mental", "failings", "stigma", "obsessive", "narcissistic",
    "health it", "am not worth", "i am sorry you", "am so stressed", "a deep breath",
    "harsh", "doctors", "to love myself", "controlling", "panic", "disturbed",
    "lose weight", "shaming", "it is my fault", "angry i", "whiny", "refused",
    "agony", "not eaten", "suffer", "terror", "does get better", "will never get over",
    "commit", "bugging", "prescription", "intention", "disgrace", "pedophiles",
    "sadness", "not defending", "urges", "xanax", "condition", "i am crying so",
    "appropriation is", "a bad person", "swear to god i", "hatred", "i am so worried",
    "attacking", "am still alive", "erasure", "drowning", "loneliness", "to swallow",
    "moan", "vomiting", "can not do this anymore", "abuse", "want to be skinny",
    "intolerant", "been clean", "hate life", "bawling", "so alone", "so scared",
    "they/them", "horrendous", "bullies", "ableism", "victim of", "lexapro",
    "androgynous", "anxious", "alone and", "not stop crying", "crying so much",
    "heroin", "failure", "my own fault", "attacks", "tired omg", "be alone",
    "feel sad", "not sleeping", "im crying so", "hate people", "drowned", "manipulate",
    "i want to cut", "masturbation", "am struggling", "how hard it is", "threatened",
    "wreck", "med", "to therapy", "in pain", "weight again", "feel so much better",
    "broke down", "worrying", "still struggle", "am losing", "am going through",
    "exploited", "escape", "to hate me", "give a shit", "this is too much",
    "reason to live", "am disgusting", "my own skin", "hate myself", "not :)",
    "bullied", "strain", "feel so fat", "look in the mirror", "raping", "gutted",
    "feel happy", "devastated", "it makes me feel", "my ed", "innocence",
    "clean from", "a waste of space", "i hate my life", "to try and sleep",
    "dizziness", "am not the only one", "abortion", "sob", "need someone to talk",
    "betrayed", "fraud", "personalities", "paranoia", "i cant do this", "abusing",
    "so sorry to", "commenting", "you realise", "want to live", "deserve to be happy",
    "be thin", "edgy", "drop dead", "flashbacks", "being fat", "sorry for your",
    "someone to talk to", "delusion", "haunt", "hate my body", "imaginary",
    "bothering", "bully", "am just sick of", "mentalhealth", "i am already dead",
    "void", "i am trash", "i have been up", "safe space", "a piece of shit",
    "are feeling better", "i can not deal with", "lucid", "overweight", "whining",
    "desperation", "consciousness", "replying", "have lost weight", "i should probably sleep"
]

# Arabic patterns (Massively Expanded with Dialects)
SUICIDE_PATTERNS_AR = [
    "انتحار", "انتحر", "اقتل نفسي", "أقتل نفسي", "اريد ان اموت", "أريد أن أموت",
    "اريد قتل نفسي", "أريد قتل نفسي", "اريد الانتحار", "أريد الانتحار",
    "لا اريد العيش", "لا أريد العيش", "لا اريد ان اعيش", "لا أريد أن أعيش",
    "لا اريد الاستمرار", "لا أريد الاستمرار", "لا اريد ان اكمل", "لا أريد أن أكمل",
    "لا سبب للعيش", "لا فائدة من الحياة", "اريد ان اختفي", "أريد أن أختفي",
    "اريد الاختفاء", "أريد الاختفاء", "لا اريد ان اكمل الحياه", "لا أريد أن أكمل الحياة",
    "افضل الموت", "أفضل الموت", "انهي حياتي", "أنهي حياتي", "سأنهي حياتي",
    "نفسي اموت", "نفسي أموت", "عايز اموت", "عايز أموت", "عايز اقتل نفسي",
    "انا عايز اقتل نفسي", "أنا عايز أقتل نفسي", "مش عايز اعيش", "مش عايز أعيش",
    "مش عايز اكمل", "مش عايز أكمل", "افكر في الانتحار", "أفكر في الانتحار",
    "اتمنى الموت", "أتمنى الموت", "اريد الموت", "أريد الموت", "بدي أموت", "بنهي حياتي",
    "كاره حياتي", "ما بدي أعيش", "بموت نفسي", "بقتل نفسي", "انهاء الحياة", "رحيل",
    "وداعا", "سامحوني", "يا رب خذني", "يا رب أموت", "يا رب ارحمني", "سفر بلا عودة",
    "انتحاري", "فكرت بالانتحار", "حاولت أنتحر", "شنق", "حبل", "قفز", "غرق", "حرق",
    "رصاص", "سلاح", "سم", "حبوب", "موت", "جنازة", "قبر", "كفن", "بدي ارتاح",
    "الدنيا ما تسوى", "خلصت حياتي", "بدي اخلص من حياتي", "عم فكر انتحر",
    "حياتي ما الها قيمة", "الموت ارحم", "بدي روح عند ربي", "الله ياخدني",
    "تعبت من كل شي", "ما عاد فيني كمل", "بدي انهي كل شي", "روحي طلعت",
    "بدي انتحر", "بدي اخلص", "مش طايق حياتي", "بدي موت", "بدي اتخلص من حياتي",
    "بدي انتحر وارتاح", "بدي اخلص من هالدنيا", "بدي اروح", "بدي غيب", "بدي اختفي"
]

SELF_HARM_PATTERNS_AR = [
    "ايذاء النفس", "إيذاء النفس", "أؤذي نفسي", "اؤذي نفسي", "اضر نفسي", "أضر نفسي",
    "اجرح نفسي", "أجرح نفسي", "اقطع نفسي", "أقطع نفسي", "اريد ايذاء نفسي",
    "أريد إيذاء نفسي", "عايز اؤذي نفسي", "عايز أؤذي نفسي", "أذيت نفسي", "بقطع عروقي",
    "شفرة", "موس", "سكين", "دم", "نزيف", "جرح", "ندبة", "آثار جروح", "تغطية الجروح",
    "بجرح ايدي", "بقطع ايدي", "بشطب جسمي", "بشطب ايدي", "بأذي حالي", "بضر حالي",
    "بدي اجرح حالي", "بدي اقطع عروقي", "بدي انزف", "بدي اتوجع", "بدي عاقب حالي"
]

DISTRESS_PATTERNS_AR = [
    "يائس", "ياس", "الياس", "اليأس", "اشعر بالياس", "أشعر باليأس",
    "بلا امل", "بلا أمل", "لا امل", "لا أمل", "لا ارى اي امل", "لا أرى أي أمل",
    "لا استطيع الاستمرار", "لا أستطيع الاستمرار", "لا اقدر على الاستمرار", "لا أقدر على الاستمرار",
    "لا اطيق", "لا أطيق", "انهيار", "متعب نفسيا", "متعب نفسياً", "فقدت الامل", "فقدت الأمل",
    "لا مخرج", "يئست", "يئس", "حزين جدا", "حزين جداً", "منهار", "منهاره",
    "مكتئب جدا", "مكتئب جداً", "اشعر بالاختناق", "أشعر بالاختناق",
    "اشعر انني عالق", "أشعر أنني عالق", "حزن شديد", "يأس", "فقدان الأمل", "وحيد",
    "منعزل", "ضيق", "مخنوق", "ببكي", "صياح", "ألم نفسي", "وجع", "قلق", "خوف",
    "فزع", "وسواس", "تفكير في الموت", "كره الذات", "أنا فاشل", "ما لي قيمة",
    "عديم الفائدة", "مشاكل نفسية", "مرض نفسي", "طبيب نفسي", "علاج نفسي",
    "أدوية اكتئاب", "مهدئات", "فقدان الرغبة", "نوم طويل", "أرق", "شهية مسدودة",
    "تعب", "إرهاق", "خمول", "عزلة", "تفكير سلبي", "ظلام", "نهاية", "جحيم",
    "عذاب", "صدمة", "تروما", "تحرش", "اغتصاب", "عنف", "ضرب", "إهانة",
    "تنمر", "فضيحة", "خيانة", "فراق", "موت", "ضايع", "تائه", "مشتت",
    "تركيز ضعيف", "نسيان", "هلوسة", "أصوات في راسي", "جنون", "فقدان العقل",
    "مستشفى المجانين", "مصحة", "انفصام", "ثنائي القطب", "هوس", "نوبة هلع",
    "خفقان", "ضيق تنفس", "اختناق", "غصة", "قلبي يوجعني", "نفسيتي تعبانة",
    "أنا زبالة", "أنا حشرة", "ما حدا يحبني", "الكل يكرهني", "وحيد تماما",
    "بموت لحالي", "بدي اختفي", "بدي أهرب", "ضياع المستقبل", "فشل دراسي",
    "فشل وظيفي", "طرد", "فقر", "ديون", "سجن", "ظلم", "قهر", "حرمان",
    "فقد", "يتم", "وحدة قاتلة", "ليل طويل", "كوابيس", "ألم لا يحتمل", "صرخة",
    "مساعدة", "انقذوني", "لحقوا علي", "بموت", "بضيع", "تحطم", "كسر",
    "شظايا", "رماد", "حطام", "تدمير", "خراب", "بوليميا", "أنوركسيا",
    "نحافة مفرطة", "سمنة مفرطة", "كره جسمي", "بشع", "قبيح", "مقرف",
    "مشمئز", "عار", "خزي", "ذنب", "تأنيب ضمير", "ندم", "توبة", "استغفار",
    "مهموم", "مهمومة", "مكسور", "مكسورة", "موجوع", "موجوعة", "تعبان",
    "تعبانة", "مخنوق", "مخنوقة", "ضايق صدري", "ضايقة فيني الدنيا",
    "ما في امل", "الدنيا سودة", "كل شي ضدبي", "ما حدا حاسس فيني",
    "بدي ارتاح", "خلص بكفي", "ما عاد فيني اتحمل", "بدي اهرب", "بدي اختفي",
    "روحي عم تطلع", "قلبي عم يتقطع", "بموت من الوجع", "حياتي تدمرت",
    "خسرت كل شي", "فشلت بكل شي", "ما الي لزمة", "وجودي غلط", "ليش انا عايش"
]

# (Other language sets remain the same as previous)
SUICIDE_PATTERNS_FR = ["suicide", "me suicider", "tuer moi", "me tuer", "veux mourir", "envie de mourir", "finir ma vie", "mettre fin à ma vie", "plus envie de vivre", "ne veux plus vivre", "je veux disparaître", "plus de raison de vivre", "la vie ne vaut pas"]
SELF_HARM_PATTERNS_FR = ["automutilation", "me faire du mal", "me blesser", "me couper", "m'automutiler", "me punir"]
DISTRESS_PATTERNS_FR = ["désespéré", "sans espoir", "ne peux plus", "effondrement", "débordé", "aucune issue", "abandonner la vie", "panique", "je me sens piégé", "épuisé émotionnellement"]

SUICIDE_PATTERNS_ES = ["suicidarme", "suicidio", "matarme", "quiero morir", "quiero morirme", "acabar con mi vida", "terminar mi vida", "no quiero vivir", "no quiero seguir viviendo", "quiero desaparecer", "no hay razón para vivir", "la vida no vale la pena"]
SELF_HARM_PATTERNS_ES = ["autolesión", "autolesionarme", "hacerme daño", "lastimarme", "cortarme", "herirme", "castigarme"]
DISTRESS_PATTERNS_ES = ["desesperado", "sin esperanza", "no puedo más", "colapso", "abrumado", "sin salida", "rendirme", "ataque de pánico", "me siento atrapado", "agotado emocionalmente"]

SUICIDE_PATTERNS_IT = ["suicidarmi", "suicidio", "uccidermi", "voglio morire", "voglio morirmi", "far finire la mia vita", "terminare la mia vita", "non voglio vivere", "non voglio più vivere", "voglio scomparire", "nessuna ragione per vivere", "la vita non vale"]
SELF_HARM_PATTERNS_IT = ["autolesionismo", "farmi del male", "ferirmi", "tagliarmi", "punirmi", "autolesionarmi"]
DISTRESS_PATTERNS_IT = ["disperato", "senza speranza", "non ce la faccio più", "crollo", "sopraffatto", "nessuna via d'uscita", "arrendermi", "attacco di panico", "mi sento intrappolato", "esausto emotivamente"]




def heuristic_crisis_classify(text: str) -> str:
  if not text or not text.strip():
    return "SAFE"

  suicide_sets = [
    (SUICIDE_PATTERNS_EN, False),
    (SUICIDE_PATTERNS_AR, True),
    (SUICIDE_PATTERNS_FR, False),
    (SUICIDE_PATTERNS_ES, False),
    (SUICIDE_PATTERNS_IT, False),
  ]
  for patterns, arabic in suicide_sets:
    if _matches_any(text, patterns, arabic=arabic):
      return "SUICIDE_RISK"

  harm_sets = [
    (SELF_HARM_PATTERNS_EN, False),
    (SELF_HARM_PATTERNS_AR, True),
    (SELF_HARM_PATTERNS_FR, False),
    (SELF_HARM_PATTERNS_ES, False),
    (SELF_HARM_PATTERNS_IT, False),
  ]
  for patterns, arabic in harm_sets:
    if _matches_any(text, patterns, arabic=arabic):
      return "SELF_HARM"

  distress_sets = [
    (DISTRESS_PATTERNS_EN, False),
    (DISTRESS_PATTERNS_AR, True),
    (DISTRESS_PATTERNS_FR, False),
    (DISTRESS_PATTERNS_ES, False),
    (DISTRESS_PATTERNS_IT, False),
  ]
  for patterns, arabic in distress_sets:
    if _matches_any(text, patterns, arabic=arabic):
      return "CRISIS_DISTRESS"

  return "SAFE"