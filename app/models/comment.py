from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    post_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    comment_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reply_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reply_failed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reused_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_comments_created_at", "created_at"),
        Index("ix_comments_emotion", "emotion"),
        Index("ix_comments_reply_sent", "reply_sent"),
    )

    def __repr__(self) -> str:
        return f"<Comment id={self.id} comment_id={self.comment_id}>"
