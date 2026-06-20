from datetime import UTC, datetime, timedelta
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_auth_session, get_current_user, get_db
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    password_hash_needs_upgrade,
    verify_password,
)
from app.db.models import AuthSession, User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
# Prevent timing differences between existing and missing users during login failure paths.
DUMMY_PASSWORD_HASH = hash_password("dummy-password")


def _get_rate_limit_key(request: Request, email: str) -> str:
    """Build a per-client-per-email rate limit key for login attempts."""
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{email.lower()}"


def _consume_login_attempt(request: Request, email: str) -> tuple[str, list[float], float]:
    """Manage the in-memory MVP login bucket and return its key, entries and timestamp."""
    settings = get_settings()
    limiter = getattr(request.app.state, "login_rate_limiter", {})
    request.app.state.login_rate_limiter = limiter

    key = _get_rate_limit_key(request, email)
    now = monotonic()
    attempts = limiter.setdefault(key, [])
    cutoff = now - settings.login_rate_limit_window_seconds
    attempts[:] = [attempt for attempt in attempts if attempt >= cutoff]
    if len(attempts) >= settings.login_rate_limit_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em alguns minutos.",
        )
    return key, attempts, now


def _reset_login_attempts(request: Request, key: str) -> None:
    """Clear the login rate limit bucket after a successful authentication."""
    limiter = getattr(request.app.state, "login_rate_limiter", {})
    limiter.pop(key, None)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    key, attempts, now = _consume_login_attempt(request, payload.email)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    stored_password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    if user is None or not verify_password(payload.password, stored_password_hash):
        attempts.append(now)
        del attempts[:-settings.login_rate_limit_attempts]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    try:
        db.execute(
            delete(AuthSession).where(AuthSession.expires_at <= datetime.now(UTC))
        )

        if password_hash_needs_upgrade(user.password_hash):
            user.password_hash = hash_password(payload.password)

        raw_token = create_access_token()
        expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)
        db.add(
            AuthSession(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=expires_at,
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    _reset_login_attempts(request, key)
    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    auth_session: AuthSession = Depends(get_current_auth_session),
    db: Session = Depends(get_db),
) -> Response:
    db.delete(auth_session)
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
