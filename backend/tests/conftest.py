"""
Shared pytest fixtures.
"""
import os

# Set required env vars before app import
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("BASE_URL", "http://testserver")
os.environ.setdefault("OTEL_ENABLED", "false")
