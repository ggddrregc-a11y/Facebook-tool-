import re
from typing import Optional

# Emotion labels in Arabic
EMOTION_LABELS = {
    "دعاء": "دعاء",
    "حزن": "حزن",
    "فرح": "فرح",
    "حب": "حب",
    "إعجاب": "إعجاب",
    "سؤال": "سؤال",
    "غضب": "غضب",
    "إيموجي": "إيموجي",
    "محايد": "محايد",
}

# Prayer / Dua keywords
PRAYER_PATTERNS = [
    r"اللهم",
    r"يا رب",
    r"ربنا",
    r"بارك الله",
    r"جزاك الله",
    r"جزاكم الله",
    r"رحمه الله",
    r"رحمك الله",
    r"يرحم",
    r"يحفظ",
    r"يوفق",
    r"آمين",
    r"أمين",
    r"حفظك الله",
    r"وفقك الله",
    r"اللهم آمين",
    r"دعاء",
    r"نسأل الله",
]

# Sadness keywords
SADNESS_PATTERNS = [
    r"حزين",
    r"حزينة",
    r"زعلان",
    r"زعلانة",
    r"مؤلم",
    r"وجع",
    r"بكيت",
    r"دموع",
    r"أتعبني",
    r"صعبة",
    r"صعب",
    r"مشكلة",
    r"تعبان",
    r"تعبانة",
    r"😢",
    r"😭",
    r"💔",
    r"🥺",
]

# Joy keywords
JOY_PATTERNS = [
    r"سعيد",
    r"سعيدة",
    r"فرحان",
    r"فرحانة",
    r"يسعد",
    r"بسعدني",
    r"الحمدلله",
    r"الحمد لله",
    r"😊",
    r"😃",
    r"😄",
    r"🎉",
    r"🥳",
    r"❤️",
]

# Love / Affection keywords
LOVE_PATTERNS = [
    r"بحبك",
    r"بحبكم",
    r"أحبك",
    r"أحبكم",
    r"حبيبي",
    r"حبيبة",
    r"❤",
    r"🤍",
    r"🧡",
    r"💛",
    r"💙",
    r"💜",
    r"💚",
    r"💗",
    r"💓",
    r"💞",
    r"💝",
]

# Like / Admiration keywords
ADMIRATION_PATTERNS = [
    r"ممتاز",
    r"رائع",
    r"جميل",
    r"جميلة",
    r"أحلى",
    r"كتير حلو",
    r"حلو",
    r"تمام",
    r"بديع",
    r"مبدع",
    r"مبدعة",
    r"شاطر",
    r"شاطرة",
    r"عظيم",
    r"👍",
    r"🔥",
    r"💯",
    r"🙌",
    r"👏",
    r"✨",
]

# Question keywords
QUESTION_PATTERNS = [
    r"\?",
    r"؟",
    r"كيف",
    r"متى",
    r"أين",
    r"وين",
    r"ليش",
    r"لماذا",
    r"ماذا",
    r"ما هو",
    r"ما هي",
    r"هل ",
    r"هل؟",
    r"من أين",
    r"من وين",
    r"فين",
    r"كمان",
    r"ازاي",
    r"امتى",
]

# Anger keywords
ANGER_PATTERNS = [
    r"غلط",
    r"خطأ",
    r"مش صح",
    r"سيء",
    r"سيئة",
    r"زبالة",
    r"مزعج",
    r"إشمعنى",
    r"مش معقول",
    r"😡",
    r"🤬",
    r"😤",
    r"👎",
]

# Pure emoji pattern
PURE_EMOJI_PATTERN = re.compile(
    r"^[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0000FE00-\U0000FEFF"
    r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
    r"\U00002702-\U000027B0\s]+$"
)


def _match_any(text: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
            return True
    return False


def detect_emotion(text: str) -> str:
    """Detect the primary emotion category of an Arabic comment."""
    stripped = text.strip()

    # Check pure emoji first
    if PURE_EMOJI_PATTERN.match(stripped):
        return "إيموجي"

    # Check in priority order
    if _match_any(stripped, PRAYER_PATTERNS):
        return "دعاء"

    if _match_any(stripped, QUESTION_PATTERNS):
        return "سؤال"

    if _match_any(stripped, ANGER_PATTERNS):
        return "غضب"

    if _match_any(stripped, SADNESS_PATTERNS):
        return "حزن"

    if _match_any(stripped, LOVE_PATTERNS):
        return "حب"

    if _match_any(stripped, JOY_PATTERNS):
        return "فرح"

    if _match_any(stripped, ADMIRATION_PATTERNS):
        return "إعجاب"

    return "محايد"
