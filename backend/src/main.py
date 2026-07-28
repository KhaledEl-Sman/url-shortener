"""
URL Shortener - Flask Application Entry Point
"""
import logging
import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger

from src.extensions import db, jwt, limiter, redis_client
from src.routes.auth import auth_bp
from src.routes.links import links_bp
from src.routes.redirect import redirect_bp
from src.routes.analytics import analytics_bp


def setup_logging():
    """Configure structured JSON logging for log shipping."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]


def setup_tracing(app: Flask):
    """Configure OpenTelemetry tracing."""
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://otel-collector:4317")

    resource = Resource.create(
        {"service.name": "url-shortener-backend", "service.version": "0.1.0"}
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()


def create_app() -> Flask:
    setup_logging()
    logger = logging.getLogger(__name__)

    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config.update(
        SECRET_KEY=os.environ["SECRET_KEY"],
        JWT_SECRET_KEY=os.environ["JWT_SECRET_KEY"],
        SQLALCHEMY_DATABASE_URI=os.environ["DATABASE_URL"],
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 300},
        RATELIMIT_STORAGE_URI=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        RATELIMIT_DEFAULT="200 per day;50 per hour",
        BASE_URL=os.environ.get("BASE_URL", "http://localhost"),
    )

    # ── Extensions ────────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    redis_client.init_app(app)

    Migrate(app, db)

    # ── Observability ─────────────────────────────────────────────────────────
    PrometheusMetrics(app, path="/metrics")
    if os.getenv("OTEL_ENABLED", "true").lower() == "true":
        setup_tracing(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(links_bp, url_prefix="/api/links")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(redirect_bp)  # handles /<short_code> at root

    # ── Health endpoint ───────────────────────────────────────────────────────
    @app.route("/health")
    @limiter.exempt
    def health():
        checks = {"status": "ok", "db": "ok", "redis": "ok"}
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            checks["db"] = "error"
            checks["status"] = "degraded"
        try:
            redis_client.client.ping()
        except Exception:
            checks["redis"] = "error"
            checks["status"] = "degraded"
        code = 200 if checks["status"] == "ok" else 503
        return jsonify(checks), code

    logger.info("Application started", extra={"env": os.getenv("FLASK_ENV", "production")})
    return app


app = create_app()
