"""Facebook Graph API client — replies, posts, and insights."""

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


# ── Comment replies ───────────────────────────────────────────────────────────

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


# ── Post publishing ───────────────────────────────────────────────────────────

async def publish_post(message: str, image_url: Optional[str] = None) -> str:
    """Publish a post to the Facebook page. Returns the new post ID."""
    settings = get_settings()
    client = get_http_client()
    page_id = settings.facebook_page_id or "me"

    try:
        if image_url:
            # Photo post
            url = f"{GRAPH_API_BASE}/{page_id}/photos"
            payload = {
                "url": image_url,
                "caption": message,
                "access_token": settings.page_access_token,
            }
        else:
            # Text post
            url = f"{GRAPH_API_BASE}/{page_id}/feed"
            payload = {
                "message": message,
                "access_token": settings.page_access_token,
            }

        response = await client.post(url, data=payload)
        data = response.json()

        if response.status_code not in (200, 201):
            error_msg = data.get("error", {}).get("message", "خطأ غير معروف")
            logger.error(
                "facebook_publish_failed",
                status_code=response.status_code,
                error=error_msg,
            )
            raise FacebookAPIException(f"فشل نشر المنشور: {error_msg}")

        post_id = data.get("post_id") or data.get("id", "")
        logger.info("facebook_post_published", post_id=post_id)
        return post_id

    except FacebookAPIException:
        raise
    except httpx.TimeoutException:
        raise FacebookAPIException("انتهت مهلة الاتصال بفيسبوك عند النشر")
    except Exception as e:
        logger.error("facebook_publish_error", error=str(e))
        raise FacebookAPIException(f"خطأ في نشر المنشور: {str(e)}")


async def get_post_insights(post_id: str) -> dict:
    """Fetch engagement insights for a published post."""
    settings = get_settings()
    client = get_http_client()

    url = f"{GRAPH_API_BASE}/{post_id}"
    params = {
        "fields": "reactions.summary(true),comments.summary(true),shares,insights.metric(post_impressions_unique)",
        "access_token": settings.page_access_token,
    }

    try:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return {}
        data = response.json()

        reactions = data.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = data.get("shares", {}).get("count", 0)
        reach = 0
        for item in data.get("insights", {}).get("data", []):
            if item.get("name") == "post_impressions_unique":
                values = item.get("values", [])
                if values:
                    reach = values[-1].get("value", 0)

        return {
            "reactions": reactions,
            "comments": comments,
            "shares": shares,
            "reach": reach,
        }
    except Exception as e:
        logger.warning("facebook_insights_error", post_id=post_id, error=str(e))
        return {}


async def get_page_posts(limit: int = 10) -> list:
    """Fetch recent posts from the page."""
    settings = get_settings()
    client = get_http_client()
    page_id = settings.facebook_page_id or "me"

    url = f"{GRAPH_API_BASE}/{page_id}/posts"
    params = {
        "fields": "id,message,created_time,reactions.summary(true),comments.summary(true),shares",
        "limit": limit,
        "access_token": settings.page_access_token,
    }

    try:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return []
        return response.json().get("data", [])
    except Exception as e:
        logger.warning("facebook_get_posts_error", error=str(e))
        return []


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
