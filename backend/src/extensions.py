"""
Shared Flask extension instances — imported by main.py and routes.
Avoids circular imports by not importing app here.
"""

import redis
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)


class RedisClient:
    """Lazy Redis wrapper that initialises after app is configured."""

    def __init__(self):
        self.client: redis.Redis | None = None

    def init_app(self, app: Flask):
        self.client = redis.Redis.from_url(
            app.config.get("RATELIMIT_STORAGE_URI", "redis://redis:6379/0"),
            decode_responses=True,
        )

    def get(self, key: str):
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int | None = None):
        self.client.set(key, value, ex=ex)

    def incr(self, key: str):
        return self.client.incr(key)

    def delete(self, key: str):
        self.client.delete(key)


redis_client = RedisClient()
