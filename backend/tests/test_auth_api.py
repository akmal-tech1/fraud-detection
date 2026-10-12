"""Authentication API tests using an isolated SQLite database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base, get_db
from main import app

REGISTER_PAYLOAD = {
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "safe-demo-password",
}


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'auth_test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    def override_get_db():
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_register_login_and_load_current_user(client):
    registered = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert registered.status_code == 201
    assert registered.json()["username"] == REGISTER_PAYLOAD["username"]
    assert registered.json()["email"] == REGISTER_PAYLOAD["email"]
    assert "password" not in registered.json()
    assert "password_hash" not in registered.json()

    logged_in = client.post(
        "/api/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]

    profile = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200
    assert profile.json()["username"] == REGISTER_PAYLOAD["username"]
    assert profile.json()["email"] == REGISTER_PAYLOAD["email"]


def test_register_normalizes_username_and_email(client):
    payload = {
        **REGISTER_PAYLOAD,
        "username": "Demo_User",
        "email": "Demo@Example.com",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["username"] == "demo_user"
    assert response.json()["email"] == "demo@example.com"


@pytest.mark.parametrize(
    "duplicate",
    [
        {"username": "demo_user", "email": "another@example.com"},
        {"username": "another_user", "email": "demo@example.com"},
    ],
)
def test_register_rejects_duplicate_username_or_email(client, duplicate):
    assert client.post("/api/auth/register", json=REGISTER_PAYLOAD).status_code == 201
    response = client.post(
        "/api/auth/register",
        json={**duplicate, "password": "another-safe-password"},
    )
    assert response.status_code == 400


def test_login_rejects_wrong_password(client):
    client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    response = client.post(
        "/api/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "incorrect"},
    )
    assert response.status_code == 401


def test_register_rejects_invalid_username_and_short_password(client):
    invalid_username = client.post(
        "/api/auth/register",
        json={**REGISTER_PAYLOAD, "username": "a b"},
    )
    assert invalid_username.status_code == 422

    short_password = client.post(
        "/api/auth/register",
        json={**REGISTER_PAYLOAD, "password": "short"},
    )
    assert short_password.status_code == 422
