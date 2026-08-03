"""
Shared pytest fixtures.
"""
import os

# Set required env vars before app import
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["BASE_URL"] = "http://testserver"
os.environ["OTEL_ENABLED"] = "false"
