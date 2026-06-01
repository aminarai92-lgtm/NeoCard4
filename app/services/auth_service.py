import logging
from datetime import datetime
from urllib.parse import urlencode

import certifi
import httpx
from sqlalchemy.orm import Session

from app.config import get_settings

logger = logging.getLogger(__name__)
from app.models.user import RefreshToken, User, UserRole
from app.schemas.user import TokenResponse, UserPublic
from app.utils.security import (
    create_access_token,
    create_refresh_token_value,
    get_refresh_expiry,
    hash_token,
)

settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_auth_url(state: str, redirect_uri: str | None = None) -> str:
    redirect = redirect_uri or settings.google_redirect_uri
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _oauth_ssl_verify() -> str | bool:
    """Use certifi CA bundle; set OAUTH_SSL_VERIFY=false in .env only for local dev SSL issues."""
    if not settings.oauth_ssl_verify:
        return False
    return certifi.where()


async def exchange_google_code(code: str, redirect_uri: str | None = None) -> dict:
    redirect = redirect_uri or settings.google_redirect_uri
    verify = _oauth_ssl_verify()
    async with httpx.AsyncClient(timeout=30.0, verify=verify) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code >= 400:
            logger.error("Google token error %s: %s", token_resp.status_code, token_resp.text)
            token_resp.raise_for_status()
        tokens = token_resp.json()
        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if user_resp.status_code >= 400:
            logger.error("Google userinfo error %s: %s", user_resp.status_code, user_resp.text)
            user_resp.raise_for_status()
        return user_resp.json()


def get_or_create_user(db: Session, google_data: dict) -> User:
    google_id = google_data["id"]
    email = google_data["email"].lower()
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    role = UserRole.admin if email in settings.admin_email_list else UserRole.user
    if user:
        user.name = google_data.get("name", user.name)
        user.avatar_url = google_data.get("picture", user.avatar_url)
        user.last_login_at = datetime.utcnow()
        if email in settings.admin_email_list:
            user.role = UserRole.admin
    else:
        user = User(
            google_id=google_id,
            email=email,
            name=google_data.get("name", email.split("@")[0]),
            avatar_url=google_data.get("picture"),
            role=role,
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_tokens(db: Session, user: User, user_agent: str | None = None) -> TokenResponse:
    access = create_access_token(user.id, extra={"role": user.role.value})
    refresh_value = create_refresh_token_value()
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_value),
        expires_at=get_refresh_expiry(),
        user_agent=user_agent,
    )
    db.add(refresh)
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_value,
        user=UserPublic.model_validate(user),
    )


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse | None:
    token_hash = hash_token(refresh_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked == False)
        .first()
    )
    if not record or record.expires_at < datetime.utcnow():
        return None
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or user.is_blocked:
        return None
    record.revoked = True
    db.commit()
    return issue_tokens(db, user, record.user_agent)


def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
    token_hash = hash_token(refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if record:
        record.revoked = True
        db.commit()
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked": True})
    db.commit()
