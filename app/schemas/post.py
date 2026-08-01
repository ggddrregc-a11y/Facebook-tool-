"""Pydantic schemas for post management."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class PostGenerateRequest(BaseModel):
    topic: Optional[str] = Field(None, description="موضوع المنشور")
    extra_instructions: Optional[str] = Field(None, description="تعليمات إضافية")
    schedule_at: Optional[datetime] = Field(None, description="وقت النشر (اختياري)")
    auto_publish: bool = Field(False, description="نشر مباشر بدون مراجعة")
    generate_image: bool = Field(False, description="توليد صورة مع المنشور")


class PostApproveRequest(BaseModel):
    schedule_at: Optional[datetime] = Field(None, description="وقت النشر (أو نشر مباشر)")
    publish_now: bool = Field(False, description="نشر فوري")


class PostRejectRequest(BaseModel):
    reason: Optional[str] = Field(None, description="سبب الرفض")


class PostUpdateRequest(BaseModel):
    content: Optional[str] = None
    topic: Optional[str] = None
    schedule_at: Optional[datetime] = None


class PostResponse(BaseModel):
    id: int
    content: str
    topic: Optional[str]
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    facebook_post_id: Optional[str]
    error_message: Optional[str]
    image_url: Optional[str]
    reactions_count: int
    comments_count: int
    shares_count: int
    reach: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    per_page: int


class PostStatsResponse(BaseModel):
    total: int
    draft: int
    pending_approval: int
    approved: int
    scheduled: int
    published: int
    failed: int
    rejected: int
    total_reactions: int
    total_comments: int
    total_shares: int
    total_reach: int


class KeyStatusItem(BaseModel):
    index: int
    key_suffix: str
    active: bool
    cooldown_seconds_left: int


class KeysStatusResponse(BaseModel):
    keys: List[KeyStatusItem]
    total_keys: int
    active_keys: int
