from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.card import CardTemplate
from app.utils.helpers import sanitize_text, sanitize_url


class ExtraLink(BaseModel):
    label: str = Field(..., max_length=100)
    url: str = Field(..., max_length=500)

    @field_validator("label")
    @classmethod
    def clean_label(cls, v: str) -> str:
        return sanitize_text(v, 100)

    @field_validator("url")
    @classmethod
    def clean_url(cls, v: str) -> str:
        return sanitize_url(v)


class CardBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date | None = None
    position: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    telegram: str | None = Field(None, max_length=100)
    instagram: str | None = Field(None, max_length=100)
    skills: list[str] = Field(default_factory=list)
    experience: str | None = Field(None, max_length=5000)
    school: str | None = Field(None, max_length=255)
    college: str | None = Field(None, max_length=255)
    university: str | None = Field(None, max_length=255)
    masters: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=5000)
    website: str | None = Field(None, max_length=500)
    extra_links: list[ExtraLink] = Field(default_factory=list)
    photo_url: str | None = Field(None, max_length=2000)
    template: CardTemplate = CardTemplate.modern_blue

    @field_validator("first_name", "last_name")
    @classmethod
    def clean_names(cls, v: str) -> str:
        return sanitize_text(v, 100)

    @field_validator("description", "experience")
    @classmethod
    def clean_long_text(cls, v: str | None) -> str | None:
        return sanitize_text(v, 5000) if v else None


class CardCreate(CardBase):
    pass


class CardUpdate(CardBase):
    is_published: bool | None = None


class CardPublic(CardBase):
    id: int
    slug: str
    user_id: int
    is_published: bool
    view_count: int
    save_count: int
    qr_scan_count: int
    created_at: datetime
    updated_at: datetime
    owner_name: str | None = None
    is_saved: bool = False

    model_config = {"from_attributes": True}


class CardListItem(BaseModel):
    id: int
    slug: str
    first_name: str
    last_name: str
    position: str | None
    photo_url: str | None
    template: CardTemplate
    is_published: bool
    view_count: int
    save_count: int
    qr_scan_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardStats(BaseModel):
    card_id: int
    views: int
    saves: int
    qr_scans: int
    activity_chart: list[dict]
    recent_views: list[dict]


class DashboardStats(BaseModel):
    cards_count: int
    total_views: int
    total_saves: int
    total_qr_scans: int
    greeting: str
    recent_cards: list[CardListItem]
    popular_cards: list[CardListItem]
    ai_recommendations: list[str]
