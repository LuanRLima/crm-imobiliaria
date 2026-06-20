from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.api.routes import auth, leads, pipeline
from app.core.config import get_settings
from app.db.session import SessionFactory
from app.services.bootstrap import seed_defaults


def create_app(session_factory: sessionmaker | None = None) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            with app.state.session_factory() as session:
                seed_defaults(session)
        except OperationalError:
            pass
        yield

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.session_factory = session_factory or SessionFactory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(leads.router, prefix=settings.api_prefix)
    app.include_router(pipeline.router, prefix=settings.api_prefix)
    return app


app = create_app()
