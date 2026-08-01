import re
from typing import Tuple

# URL patterns
URL_PATTERN = re.compile(
    r"(https?://|www\.|bit\.ly|t\.co|tinyurl|http)",
    re.IGNORECASE,
)

# Repeated character pattern (e.g., "ههههههه" or "اااااااا")
REPEATED_CHARS_PATTERN = re.compile(r"(.)\1{4,}", re.UNICODE)

# Phone number pattern
PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-]{8,}\d")

# Promotional keywords
PROMO_PATTERNS = [
    r"واتساب",
    r"whatsapp",
    r"تلغرام",
    r"telegram",
    r"انستغرام",
    r"instagram",
    r"للتواصل",
    r"للتوصيل",
    r"للبيع",
    r"اشتري",
    r"اشترِ",
    r"سعر",
    r"أسعار",
    r"متجر",
    r"اطلب الآن",
    r"اضغط هنا",
    r"click here",
    r"free",
    r"مجاني",
    r"ربح",
    r"تريد ربح",
    r"دولار",
]

# Garbage / meaningless patterns
GARBAGE_PATTERNS = re.compile(
    r"^[a-zA-Z\d\s\.\,\!\?\-\_\@\#\$\%\^\&\*\(\)\+\=]{1,5}$"
)

# Minimum word length
MIN_WORDS = 1
MIN_CHARS = 2


def is_spam(text: str) -> Tuple[bool, str]:
    """
    Returns (is_spam: bool, reason: str)
    """
    stripped = text.strip()

    if len(stripped) < MIN_CHARS:
        return True, "تعليق فارغ أو قصير جداً"

    if URL_PATTERN.search(stripped):
        return True, "يحتوي على رابط"

    if PHONE_PATTERN.search(stripped):
        return True, "يحتوي على رقم هاتف"

    if REPEATED_CHARS_PATTERN.search(stripped):
        return True, "أحرف متكررة مفرطة"

    for pattern in PROMO_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE | re.UNICODE):
            return True, f"محتوى ترويجي: {pattern}"

    # Check if entirely garbage (only ASCII symbols, very short)
    if len(stripped) <= 5 and GARBAGE_PATTERNS.match(stripped):
        return True, "محتوى غير ذي معنى"

    return False, ""
