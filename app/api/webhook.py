from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.core.security import verify_facebook_signature
from app.workers.background_worker import schedule_comment_processing

logger = get_logger(__name__)
router = APIRouter(tags=["Webhook"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    """Facebook webhook verification endpoint."""
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
        logger.info("webhook_verified")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning(
        "webhook_verification_failed",
        mode=hub_mode,
        token_match=(hub_verify_token == settings.verify_token),
    )
    raise HTTPException(status_code=403, detail="التحقق فشل")


@router.post("/webhook")
async def receive_webhook(request: Request) -> Response:
    """
    Receive Facebook webhook events.
    Returns HTTP 200 immediately and processes in background.
    """
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_facebook_signature(body, signature):
        logger.warning(
            "webhook_invalid_signature",
            signature_present=bool(signature),
            signature_prefix=signature[:30] if signature else "EMPTY",
            body_length=len(body),
        )
        # Return 200 to avoid Facebook retries for invalid signatures
        return Response(content="ok", status_code=200)

    logger.info("webhook_signature_ok", body_length=len(body))

    try:
        payload = await request.json()
    except Exception:
        logger.error("webhook_invalid_json")
        return Response(content="ok", status_code=200)

    if payload.get("object") != "page":
        return Response(content="ok", status_code=200)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "feed":
                continue

            value = change.get("value", {})
            item_type = value.get("item", "")
            verb = value.get("verb", "")

            # Only process comments (new or edited)
            if item_type != "comment":
                continue

            if verb not in ("add", "edited"):
                continue

            comment_id = value.get("comment_id", "")
            post_id = value.get("post_id", "")
            sender_info = value.get("from", {})
            sender_id = sender_info.get("id", "")
            sender_name = sender_info.get("name", None)
            comment_text = value.get("message", "").strip()

            if not comment_id or not comment_text:
                logger.debug("webhook_skip_empty", comment_id=comment_id)
                continue

            logger.info(
                "webhook_comment_received",
                comment_id=comment_id,
                post_id=post_id,
                verb=verb,
                text_preview=comment_text[:50],
            )

            # Schedule background processing - returns 200 immediately
            schedule_comment_processing(
                comment_id=comment_id,
                post_id=post_id,
                sender_id=sender_id,
                sender_name=sender_name,
                comment_text=comment_text,
                is_edited=(verb == "edited"),
            )

    return Response(content="ok", status_code=200)
