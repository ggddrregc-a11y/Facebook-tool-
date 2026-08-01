from fastapi import APIRouter, Depends

from app.ai.emotion_detector import detect_emotion
from app.ai.provider import generate_reply
from app.ai.spam_detector import is_spam
from app.middlewares.auth_middleware import require_admin
from app.schemas.stats import ReplyTestRequest, ReplyTestResponse

router = APIRouter(prefix="/api", tags=["Reply Test"])


@router.post("/reply-test", response_model=ReplyTestResponse)
async def test_reply(
    request: ReplyTestRequest,
    _user: dict = Depends(require_admin),
) -> ReplyTestResponse:
    """Test AI reply generation without posting to Facebook."""
    spam_result, _ = is_spam(request.comment_text)
    emotion = detect_emotion(request.comment_text)

    if spam_result:
        return ReplyTestResponse(
            comment_text=request.comment_text,
            emotion=emotion,
            ai_reply="[تعليق مرفوض - سبام]",
            is_spam=True,
        )

    ai_reply = await generate_reply(request.comment_text, emotion)
    return ReplyTestResponse(
        comment_text=request.comment_text,
        emotion=emotion,
        ai_reply=ai_reply,
        is_spam=False,
    )
