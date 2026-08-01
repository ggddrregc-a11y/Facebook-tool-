"""
AI Provider with multi-key Grok rotation.

Keys are tried in order. When a key hits a rate-limit (429) or quota error the
system marks it as exhausted and falls over to the next available key
automatically. The exhaustion state resets after `KEY_COOLDOWN_SECONDS`.
"""

import asyncio
import re
import time
from typing import Optional

from openai import AsyncOpenAI, RateLimitError, APIStatusError

from app.config.settings import get_settings
from app.core.exceptions import AIProviderException
from app.core.logging import get_logger

logger = get_logger(__name__)

KEY_COOLDOWN_SECONDS = 60  # cooldown before retrying an exhausted key

# Per-key state: {api_key: exhausted_until_timestamp}
_key_exhausted_until: dict[str, float] = {}
_lock = asyncio.Lock()


def _get_active_keys() -> list[str]:
    """Return keys that are not currently cooling down."""
    settings = get_settings()
    now = time.monotonic()
    active = [
        k for k in settings.all_grok_keys
        if now >= _key_exhausted_until.get(k, 0)
    ]
    if not active:
        # All keys are cooling down — return all and let it fail gracefully
        return settings.all_grok_keys
    return active


def _mark_key_exhausted(key: str) -> None:
    _key_exhausted_until[key] = time.monotonic() + KEY_COOLDOWN_SECONDS
    logger.warning("grok_key_exhausted", key_suffix=key[-6:] if len(key) > 6 else "***")


def _build_client(api_key: str) -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=api_key,
        base_url=settings.grok_base_url,
    )


async def _call_with_rotation(
    messages: list[dict],
    max_tokens: int,
    temperature: float,
    system_prompt: Optional[str] = None,
) -> str:
    """Try each active key in turn; rotate on rate-limit errors."""
    settings = get_settings()
    keys = _get_active_keys()

    if not keys:
        raise AIProviderException("لا توجد مفاتيح Grok API متاحة")

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    last_error: Optional[Exception] = None

    for key in keys:
        client = _build_client(key)
        try:
            response = await client.chat.completions.create(
                model=settings.grok_model or settings.model_name,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            await client.close()

            content = response.choices[0].message.content or ""
            logger.info(
                "grok_reply_ok",
                key_suffix=key[-6:] if len(key) > 6 else "***",
                tokens=response.usage.total_tokens if response.usage else 0,
            )
            return content

        except RateLimitError as e:
            _mark_key_exhausted(key)
            last_error = e
            await client.close()
            logger.warning("grok_rate_limit", key_suffix=key[-6:] if len(key) > 6 else "***")
            continue

        except APIStatusError as e:
            if e.status_code in (429, 402, 403):
                _mark_key_exhausted(key)
                last_error = e
                await client.close()
                continue
            await client.close()
            raise AIProviderException(f"خطأ من Grok API: {e.message}")

        except Exception as e:
            await client.close()
            last_error = e
            logger.error("grok_error", error=str(e))
            raise AIProviderException(f"خطأ في الاتصال بـ Grok: {str(e)}")

    raise AIProviderException(
        f"جميع مفاتيح Grok API وصلت للحد الأقصى. آخر خطأ: {str(last_error)}"
    )


def _clean_reply(text: str) -> str:
    """Strip thinking blocks and extract the actual reply."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    arabic = re.findall(r"[\u0600-\u06FF][^\n]*", text)
    if arabic:
        text = arabic[-1].strip()
    text = text.strip('"\'«»"')
    return text.strip()


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_reply(comment_text: str, emotion: Optional[str] = None) -> str:
    """Generate a short comment reply using Grok."""
    settings = get_settings()
    user_content = comment_text
    if emotion:
        user_content = f"[المشاعر: {emotion}]\n{comment_text}"

    raw = await _call_with_rotation(
        messages=[{"role": "user", "content": user_content}],
        max_tokens=settings.ai_max_tokens,
        temperature=settings.ai_temperature,
        system_prompt=settings.system_prompt,
    )
    reply = _clean_reply(raw)
    if not reply:
        raise AIProviderException("استجابة فارغة من Grok")
    return reply


async def generate_post(topic: Optional[str] = None, extra_instructions: Optional[str] = None) -> str:
    """Generate a Facebook post using Grok."""
    settings = get_settings()
    prompt = "اكتب منشوراً جذاباً لصفحة Remix على فيسبوك."
    if topic:
        prompt += f" الموضوع: {topic}."
    if extra_instructions:
        prompt += f" تعليمات إضافية: {extra_instructions}."

    raw = await _call_with_rotation(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=settings.post_max_tokens,
        temperature=settings.post_temperature,
        system_prompt=settings.post_system_prompt,
    )
    return raw.strip()


async def generate_image_prompt(post_content: str) -> str:
    """Generate a DALL-E image prompt from a Facebook post text."""
    raw = await _call_with_rotation(
        messages=[
            {
                "role": "user",
                "content": (
                    f"بناءً على هذا المنشور:\n{post_content}\n\n"
                    "اكتب وصفاً بالإنجليزية لصورة مناسبة له (جملة واحدة فقط بالإنجليزية)."
                ),
            }
        ],
        max_tokens=100,
        temperature=0.7,
    )
    return raw.strip()


def get_keys_status() -> list[dict]:
    """Return status of all configured keys (for dashboard display)."""
    settings = get_settings()
    now = time.monotonic()
    result = []
    for i, key in enumerate(settings.all_grok_keys, start=1):
        exhausted_until = _key_exhausted_until.get(key, 0)
        is_exhausted = now < exhausted_until
        result.append(
            {
                "index": i,
                "key_suffix": f"...{key[-6:]}" if len(key) > 6 else "***",
                "active": not is_exhausted,
                "cooldown_seconds_left": max(0, int(exhausted_until - now)) if is_exhausted else 0,
            }
        )
    return result


async def close_ai_client() -> None:
    """No-op — clients are created per-request."""
    pass
