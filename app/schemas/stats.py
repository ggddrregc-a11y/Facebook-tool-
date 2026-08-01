from datetime import date
from typing import Optional
from pydantic import BaseModel


class EmotionStat(BaseModel):
    emotion: str
    count: int
    label: str


class DashboardStats(BaseModel):
    total_comments: int
    total_replies: int
    failed_replies: int
    today_comments: int
    spam_comments: int
    duplicate_comments: int
    emotion_stats: list[EmotionStat]


class DailyStatResponse(BaseModel):
    stat_date: date
    emotion: str
    count: int

    model_config = {"from_attributes": True}


class LogResponse(BaseModel):
    id: int
    level: str
    event: str
    message: Optional[str] = None
    source: Optional[str] = None
    comment_id: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[LogResponse]


class ReplyTestRequest(BaseModel):
    comment_text: str


class ReplyTestResponse(BaseModel):
    comment_text: str
    emotion: str
    ai_reply: str
    is_spam: bool
