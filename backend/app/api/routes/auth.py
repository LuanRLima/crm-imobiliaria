from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_token, verify_password
from app.db.models import AuthSession, User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    db.execute(
        delete(AuthSession).where(AuthSession.expires_at <= datetime.now(UTC))
    )

    raw_token = create_access_token()
    expires_at = datetime.now(UTC) + timedelta(hours=12)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
    )
    db.commit()

    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
