from datetime import datetime

from pydantic import BaseModel, Field

from app.models.report import ReportStatus
from app.models.user import UserRole


class AdminUserItem(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    is_blocked: bool
    cards_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminCardItem(BaseModel):
    id: int
    slug: str
    first_name: str
    last_name: str
    user_id: int
    owner_email: str
    is_published: bool
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemStats(BaseModel):
    users_count: int
    cards_count: int
    published_cards: int
    total_views: int
    pending_reports: int


class ReportCreate(BaseModel):
    card_id: int | None = None
    target_user_id: int | None = None
    reason: str = Field(..., min_length=3, max_length=100)
    details: str | None = Field(None, max_length=2000)


class ReportItem(BaseModel):
    id: int
    reason: str
    details: str | None
    status: ReportStatus
    card_id: int | None
    target_user_id: int | None
    reporter_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
