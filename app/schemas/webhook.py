from typing import Any, Optional
from pydantic import BaseModel


class FacebookValue(BaseModel):
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    verb: Optional[str] = None
    from_: Optional[dict] = None
    message: Optional[str] = None
    parent_id: Optional[str] = None

    model_config = {"populate_by_name": True}


class FacebookChange(BaseModel):
    value: Any
    field: str


class FacebookEntry(BaseModel):
    id: str
    time: int
    changes: list[FacebookChange] = []


class FacebookWebhookPayload(BaseModel):
    object: str
    entry: list[FacebookEntry] = []
