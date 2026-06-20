from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import sessionmaker

from app.core.security import BCRYPT_PREFIX, hash_password
from app.db.models import Base
from app.db.models import Lead, PipelineStage, User
from app.db.session import build_engine
from app.main import create_app
from app.services.bootstrap import seed_defaults

ADMIN_EMAIL = "admin@crmimobiliaria.local"
ADMIN_PASSWORD = "Admin123!"


def build_client(database_url: str) -> TestClient:
    engine = build_engine(database_url)
    Base.metadata.create_all(bind=engine)
    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    with testing_session_factory() as session:
        seed_defaults(session)

    app = create_app(testing_session_factory)
    return TestClient(app)


def login(
    client: TestClient,
    email: str = ADMIN_EMAIL,
    password: str = ADMIN_PASSWORD,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}


def legacy_hash_password(password: str) -> str:
    """Generate a legacy PBKDF2 hash so migration compatibility can be tested."""
    salt = b"legacy-salt"
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{urlsafe_b64encode(salt).decode()}${digest.hex()}"


def test_healthcheck(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'health.db'}")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Request-ID"]


def test_login_success_and_failure(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'auth.db'}")

    success = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    failure = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrong-password"},
    )

    assert success.status_code == 200
    assert success.json()["token_type"] == "bearer"
    assert failure.status_code == 401
    assert success.json()["user"]["role"] == "manager"


def test_login_rehashes_legacy_password_and_logout_revokes_session(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'auth-logout.db'}")

    with client.app.state.session_factory() as session:
        admin = session.scalar(select(User).where(User.email == ADMIN_EMAIL))
        assert admin is not None
        admin.password_hash = legacy_hash_password(ADMIN_PASSWORD)
        session.commit()

    headers = login(client)
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    me_response = client.get("/api/v1/auth/me", headers=headers)

    assert logout_response.status_code == 204
    assert me_response.status_code == 401

    with client.app.state.session_factory() as session:
        admin = session.scalar(select(User).where(User.email == ADMIN_EMAIL))
        assert admin is not None
        assert admin.password_hash.startswith(BCRYPT_PREFIX)


def test_login_rate_limit_blocks_repeated_failures(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'rate-limit.db'}")

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrong-password"},
    )

    assert blocked.status_code == 429
    assert blocked.json()["detail"].startswith("Muitas tentativas")


def test_create_and_list_leads(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'leads.db'}")
    headers = login(client)

    created = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "name": "Maria Cliente",
            "email": "maria@cliente.com",
            "source": "landing-page",
        },
    )
    listed = client.get("/api/v1/leads", headers=headers)

    assert created.status_code == 201
    assert created.json()["current_stage"] == "Novo Lead"
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_lead_rolls_back_without_active_stage(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'lead-rollback.db'}")
    headers = login(client)

    with client.app.state.session_factory() as session:
        session.execute(delete(PipelineStage))
        session.commit()

    created = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "name": "Maria Cliente",
            "email": "maria@cliente.com",
            "source": "landing-page",
        },
    )

    assert created.status_code == 409
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count(Lead.id))) == 0


def test_move_lead_between_stages(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'pipeline.db'}")
    headers = login(client)

    created = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "name": "João Lead",
            "phone": "11999999999",
            "source": "whatsapp",
        },
    )
    stages = client.get("/api/v1/pipeline/stages", headers=headers).json()
    moved = client.post(
        f"/api/v1/pipeline/leads/{created.json()['id']}/move",
        headers=headers,
        json={"stage_id": stages[1]["id"]},
    )
    board = client.get("/api/v1/pipeline/board", headers=headers).json()

    assert moved.status_code == 200
    assert moved.json()["name"] == "Contato Realizado"
    assert board["stages"][1]["leads"][0]["name"] == "João Lead"


def test_move_lead_rejects_inactive_stage(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'pipeline-invalid.db'}")
    headers = login(client)

    created = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "name": "João Lead",
            "phone": "11999999999",
            "source": "whatsapp",
        },
    )
    stages = client.get("/api/v1/pipeline/stages", headers=headers).json()

    with client.app.state.session_factory() as session:
        inactive_stage = session.get(PipelineStage, stages[1]["id"])
        assert inactive_stage is not None
        inactive_stage.is_active = False
        session.commit()

    moved = client.post(
        f"/api/v1/pipeline/leads/{created.json()['id']}/move",
        headers=headers,
        json={"stage_id": stages[1]["id"]},
    )
    listed = client.get("/api/v1/leads", headers=headers)

    assert moved.status_code == 404
    assert listed.json()[0]["current_stage"] == "Novo Lead"


def test_only_manager_can_create_stage(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'rbac.db'}")

    with client.app.state.session_factory() as session:
        session.add(
            User(
                name="Corretor",
                email="broker@crmimobiliaria.local",
                role="broker",
                password_hash=hash_password(ADMIN_PASSWORD),
            )
        )
        session.commit()

    headers = login(client, email="broker@crmimobiliaria.local")
    created = client.post(
        "/api/v1/pipeline/stages",
        headers=headers,
        json={"name": "Documentação", "position": 6},
    )

    assert created.status_code == 403
    assert created.json()["detail"].startswith("Permissão insuficiente")
