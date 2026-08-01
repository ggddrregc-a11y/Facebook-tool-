import asyncio
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config.settings import get_settings
from app.core.exceptions import AIProviderException
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_ai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=30.0,
            max_retries=2,
        )
    return _client


async def generate_reply(comment_text: str, emotion: str) -> str:
    """Generate an AI reply for a given comment."""
    settings = get_settings()
    client = get_ai_client()

    # Build context-aware user message
    emotion_context = {
        "دعاء": "هذا التعليق دعاء. رد بدعاء مناسب ومختصر.",
        "حزن": "هذا التعليق يعبر عن حزن. تعاطف بإيجاز واحترام.",
        "فرح": "هذا التعليق يعبر عن فرح. شارك الفرح بإيجاز.",
        "حب": "هذا التعليق يعبر عن حب. رد بدفء وإيجاز.",
        "إعجاب": "هذا التعليق إعجاب أو مدح. اشكر المستخدم بإيجاز.",
        "سؤال": "هذا التعليق سؤال. أجب باختصار إن أمكن.",
        "غضب": "هذا التعليق يعبر عن غضب. رد بهدوء واحترام دون جدال.",
        "إيموجي": "هذا التعليق إيموجي فقط. رد بشكل طبيعي ومختصر.",
        "محايد": "هذا التعليق محايد. رد بشكل طبيعي ومختصر.",
    }

    context_hint = emotion_context.get(emotion, "رد بشكل طبيعي ومختصر.")
    user_message = f"التعليق: {comment_text}\n{context_hint}"

    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": settings.system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.ai_max_tokens,
            temperature=settings.ai_temperature,
        )

        choice = response.choices[0]
        reply = choice.message.content

        # Some models return reasoning only — fallback to reasoning content
        if not reply or not reply.strip():
            reasoning = getattr(choice.message, "reasoning", None)
            if reasoning and reasoning.strip():
                # Extract last sentence from reasoning as reply
                lines = [l.strip() for l in reasoning.strip().split("\n") if l.strip()]
                reply = lines[-1] if lines else None

        if not reply or not reply.strip():
            raise AIProviderException("استجابة فارغة من مزود الذكاء الاصطناعي")

        # Clean up the reply
        reply = reply.strip()
        # Remove any leading/trailing quotes
        if reply.startswith(('"', "'", "«")) and reply.endswith(('"', "'", "»")):
            reply = reply[1:-1].strip()

        logger.info(
            "ai_reply_generated",
            emotion=emotion,
            reply_length=len(reply),
            model=settings.model_name,
        )
        return reply

    except AIProviderException:
        raise
    except Exception as e:
        logger.error("ai_provider_error", error=str(e), model=settings.model_name)
        raise AIProviderException(f"خطأ في مزود الذكاء الاصطناعي: {str(e)}")


async def close_ai_client() -> None:
    global _client
    if _client:
        await _client.close()
        _client = None
