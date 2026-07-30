"""
Shared pytest fixtures. Uses an in-memory SQLite DB so the test suite has
no external dependencies (no running Postgres needed).
"""
import pytest
from app.api.deps import get_db
from app.db.base_class import Base
from app.db.init_db import seed_roles
from app.main import app

# Import models so Base.metadata knows about every table
from app.models import monitoring, operations, role, user  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    seed_roles(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(client):
    """Registers a viewer user and returns Authorization headers for it."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture-user@example.com",
            "full_name": "Fixture User",
            "password": "SuperSecret123",
            "role": "viewer",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "fixture-user@example.com", "password": "SuperSecret123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(client):
    """Registers an admin user and returns Authorization headers for it."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture-admin@example.com",
            "full_name": "Fixture Admin",
            "password": "SuperSecret123",
            "role": "admin",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "fixture-admin@example.com", "password": "SuperSecret123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
