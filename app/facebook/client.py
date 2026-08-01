from typing import Optional

import httpx

from app.config.settings import get_settings
from app.core.exceptions import FacebookAPIException
from app.core.logging import get_logger

logger = get_logger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _http_client


async def send_comment_reply(comment_id: str, message: str) -> str:
    """Reply to a Facebook comment. Returns the new reply ID."""
    settings = get_settings()
    client = get_http_client()

    url = f"{GRAPH_API_BASE}/{comment_id}/comments"
    payload = {
        "message": message,
        "access_token": settings.page_access_token,
    }

    try:
        response = await client.post(url, data=payload)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "خطأ غير معروف")
            logger.error(
                "facebook_reply_failed",
                comment_id=comment_id,
                status_code=response.status_code,
                error=error_msg,
            )
            raise FacebookAPIException(f"فشل إرسال الرد على فيسبوك: {error_msg}")

        reply_id = data.get("id", "")
        logger.info("facebook_reply_sent", comment_id=comment_id, reply_id=reply_id)
        return reply_id

    except FacebookAPIException:
        raise
    except httpx.TimeoutException:
        logger.error("facebook_reply_timeout", comment_id=comment_id)
        raise FacebookAPIException("انتهت مهلة الاتصال بفيسبوك")
    except Exception as e:
        logger.error("facebook_client_error", error=str(e))
        raise FacebookAPIException(f"خطأ في الاتصال بفيسبوك: {str(e)}")


async def get_comment_details(comment_id: str) -> Optional[dict]:
    """Fetch comment details from Facebook Graph API."""
    settings = get_settings()
    client = get_http_client()

    url = f"{GRAPH_API_BASE}/{comment_id}"
    params = {
        "fields": "id,message,from,created_time",
        "access_token": settings.page_access_token,
    }

    try:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.warning("facebook_get_comment_error", error=str(e))
        return None


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
