from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.db.models import AuthSession, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db(request: Request):
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_current_auth_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthSession:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória.",
        )

    token_hash = hash_token(credentials.credentials)
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.expires_at > datetime.now(UTC),
        )
    )

    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    return auth_session


def get_current_user(
    auth_session: AuthSession = Depends(get_current_auth_session),
) -> User:
    return auth_session.user


def require_roles(*roles: str):
    """Build a dependency that only allows authenticated users with the given roles."""
    allowed_roles = set(roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        """Validate the current user role against the allowed RBAC set."""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente para esta operação.",
            )
        return current_user

    return dependency
