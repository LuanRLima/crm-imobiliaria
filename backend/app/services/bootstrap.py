from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import PipelineStage, User


def seed_defaults(db: Session) -> None:
    settings = get_settings()

    existing_admin = db.scalar(select(User).where(User.email == settings.seed_admin_email))
    if existing_admin is None:
        db.add(
            User(
                name="Administrador",
                email=settings.seed_admin_email,
                role="manager",
                password_hash=hash_password(settings.seed_admin_password),
            )
        )

    if db.scalar(select(PipelineStage.id)) is None:
        db.add_all(
            [
                PipelineStage(name="Novo Lead", position=1),
                PipelineStage(name="Contato Realizado", position=2),
                PipelineStage(name="Visita Agendada", position=3),
                PipelineStage(name="Proposta", position=4),
                PipelineStage(name="Fechado", position=5),
            ]
        )

    db.commit()
