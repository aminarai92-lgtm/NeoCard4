from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    name: str
    avatar_url: str | None
    role: UserRole
    onboarding_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class GoogleAuthURLRequest(BaseModel):
    redirect_uri: str | None = None


class GoogleAuthURLResponse(BaseModel):
    auth_url: str


class OnboardingComplete(BaseModel):
    completed: bool = True
