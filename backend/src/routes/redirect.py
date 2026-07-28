"""
Redirect route: GET /<short_code>
Redis cache-first, then PostgreSQL. Records click in DB.
"""
import logging

from flask import Blueprint, jsonify, redirect, request

from src.extensions import db, redis_client
from src.models import Click, Link

redirect_bp = Blueprint("redirect", __name__)
logger = logging.getLogger(__name__)

CACHE_TTL = 300


@redirect_bp.route("/<string:short_code>")
def resolve(short_code: str):
    cache_key = f"redirect:{short_code}"

    # 1. Try Redis cache first
    cached = redis_client.get(cache_key)
    if cached:
        _record_click(short_code, request)
        logger.info("redirect cache hit", extra={"short_code": short_code})
        return redirect(cached, code=302)

    # 2. Fall back to DB
    link = Link.query.filter_by(short_code=short_code, is_active=True).first()
    if not link:
        return jsonify({"error": "link not found"}), 404

    # Warm cache for next time
    redis_client.set(cache_key, link.original_url, ex=CACHE_TTL)
    _record_click(short_code, request, link_id=link.id)
    logger.info("redirect db hit", extra={"short_code": short_code})
    return redirect(link.original_url, code=302)


def _record_click(short_code: str, req, link_id: int | None = None):
    """Async-safe click recording — fires and DB commits independently."""
    try:
        if link_id is None:
            link = Link.query.filter_by(short_code=short_code).first()
            if not link:
                return
            link_id = link.id

        click = Click(
            link_id=link_id,
            ip_address=req.remote_addr,
            user_agent=req.user_agent.string[:512] if req.user_agent.string else None,
            referer=req.referrer[:1024] if req.referrer else None,
        )
        db.session.add(click)
        db.session.commit()

        # Increment Redis counter for fast analytics
        redis_client.incr(f"clicks:{short_code}:total")
    except Exception as exc:
        logger.error("click recording failed", extra={"error": str(exc), "short_code": short_code})
        db.session.rollback()
