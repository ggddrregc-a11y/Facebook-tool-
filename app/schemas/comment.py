from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    comment_id: str
    post_id: str
    sender_id: str
    sender_name: Optional[str] = None
    comment_text: str


class CommentCreate(CommentBase):
    is_edited: bool = False


class CommentResponse(CommentBase):
    id: int
    comment_hash: str
    emotion: Optional[str] = None
    ai_reply: Optional[str] = None
    reply_sent: bool
    reply_failed: bool
    is_spam: bool
    is_duplicate: bool
    is_edited: bool
    reused_reply: bool
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[CommentResponse]


class CommentSearchParams(BaseModel):
    q: Optional[str] = None
    emotion: Optional[str] = None
    reply_sent: Optional[bool] = None
    is_spam: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
