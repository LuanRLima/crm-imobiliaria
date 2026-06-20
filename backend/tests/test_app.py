from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session import build_engine
from app.main import create_app
from app.services.bootstrap import seed_defaults


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


def login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@crmimobiliaria.local", "password": "Admin123!"},
    )
    token = response.json()["access_token"]
    return {"Authorization": "Bearer " + token}


def test_healthcheck(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'health.db'}")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success_and_failure(tmp_path):
    client = build_client(f"sqlite:///{tmp_path / 'auth.db'}")

    success = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@crmimobiliaria.local", "password": "Admin123!"},
    )
    failure = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@crmimobiliaria.local", "password": "senha-incorreta"},
    )

    assert success.status_code == 200
    assert success.json()["token_type"] == "bearer"
    assert failure.status_code == 401


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
