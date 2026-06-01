import logging
import secrets
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    GoogleAuthURLResponse,
    OnboardingComplete,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)
from app.services import auth_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()
logger = logging.getLogger(__name__)


def _auth_error_redirect(message: str) -> RedirectResponse:
    frontend = settings.frontend_url.rstrip("/")
    return RedirectResponse(
        url=f"{frontend}/pages/auth-callback.html?error={quote(message)}"
    )


@router.get("/google/url", response_model=GoogleAuthURLResponse)
def google_auth_url(redirect_uri: str | None = None):
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(16)
    return GoogleAuthURLResponse(auth_url=auth_service.get_google_auth_url(state, redirect_uri))


@router.get("/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    redirect_uri: str | None = None,
):
    try:
        google_data = await auth_service.exchange_google_code(code, redirect_uri)
    except httpx.HTTPStatusError as e:
        logger.exception("Google OAuth HTTP error")
        if e.response.status_code == 400 and "invalid_grant" in e.response.text:
            return _auth_error_redirect("Код входа уже использован. Нажмите «Войти через Google» ещё раз.")
        return _auth_error_redirect("Ошибка Google OAuth. Проверьте Client ID, Secret и Redirect URI в .env")
    except Exception as e:
        logger.exception("Google OAuth failed: %s", e)
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
            return _auth_error_redirect("Ошибка SSL. В .env должно быть: OAUTH_SSL_VERIFY=false")
        return _auth_error_redirect("Не удалось войти через Google. Попробуйте снова.")
    user = auth_service.get_or_create_user(db, google_data)
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")
    tokens = auth_service.issue_tokens(db, user, request.headers.get("user-agent"))
    frontend = settings.frontend_url.rstrip("/")
    # Tokens in URL hash (not query) — avoids JWT '+' being parsed as space
    return RedirectResponse(
        url=f"{frontend}/pages/auth-callback.html"
        f"#access_token={quote(tokens.access_token)}"
        f"&refresh_token={quote(tokens.refresh_token)}"
    )


class GoogleCodeRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


@router.post("/google/token", response_model=TokenResponse)
async def google_token_exchange(
    body: GoogleCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    code = body.code
    redirect_uri = body.redirect_uri
    try:
        google_data = await auth_service.exchange_google_code(code, redirect_uri)
    except httpx.HTTPStatusError as e:
        detail = "Google authentication failed"
        if e.response.status_code == 400 and "invalid_grant" in e.response.text:
            detail = "Authorization code expired or already used. Please login again."
        raise HTTPException(status_code=400, detail=detail) from e
    except Exception as e:
        logger.exception("Google token exchange failed")
        detail = "Google authentication failed"
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            detail = "SSL error. Set OAUTH_SSL_VERIFY=false in .env for local dev"
        raise HTTPException(status_code=400, detail=detail) from e
    user = auth_service.get_or_create_user(db, google_data)
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")
    return auth_service.issue_tokens(db, user, request.headers.get("user-agent"))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    result = auth_service.refresh_access_token(db, body.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return result


@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_service.revoke_refresh_token(db, body.refresh_token)
    return {"detail": "Logged out successfully"}


@router.post("/logout-all")
def logout_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_service.revoke_all_user_tokens(db, user.id)
    return {"detail": "All sessions revoked"}


@router.get("/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/onboarding", response_model=UserPublic)
def complete_onboarding(
    body: OnboardingComplete,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.onboarding_completed = body.completed
    db.commit()
    db.refresh(user)
    return user
