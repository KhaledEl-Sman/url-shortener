"""
Unit tests for auth routes.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from src.main import create_app
from src.extensions import db as _db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "SECRET_KEY": "test-secret",
        "RATELIMIT_ENABLED": False,
        "OTEL_ENABLED": "false",
        "BASE_URL": "http://testserver",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_success(client):
    resp = client.post("/api/auth/register", json={"email": "user@test.com", "password": "password123"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "user@test.com"


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "password123"})
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={"email": "user@test.com", "password": "short"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "login@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "login@test.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"email": "login2@test.com", "password": "password123"})
    resp = client.post("/api/auth/login", json={"email": "login2@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code in (200, 503)  # may be 503 without real DB/Redis
