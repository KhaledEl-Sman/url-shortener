"""
Links routes: create / list / delete short links
POST   /api/links          create
GET    /api/links          list user's links
DELETE /api/links/<code>   delete
"""

import logging
import os

import shortuuid
import validators
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.extensions import db, limiter, redis_client
from src.models import Link

links_bp = Blueprint("links", __name__)
logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 min
BASE_URL = os.environ.get("BASE_URL", "http://localhost")


def _cache_key(short_code: str) -> str:
    return f"redirect:{short_code}"


@links_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("50 per hour")
def create_link():
    data = request.get_json(silent=True) or {}
    original_url = (data.get("original_url") or "").strip()
    custom_code = (data.get("custom_code") or "").strip() or None
    title = (data.get("title") or "").strip() or None

    if not original_url:
        return jsonify({"error": "original_url is required"}), 400
    if not validators.url(original_url):
        return jsonify({"error": "invalid URL"}), 400

    short_code = custom_code or shortuuid.ShortUUID().random(length=7)
    if Link.query.filter_by(short_code=short_code).first():
        return jsonify({"error": "short code already taken"}), 409

    user_id = int(get_jwt_identity())
    link = Link(
        short_code=short_code,
        original_url=original_url,
        title=title,
        user_id=user_id,
    )
    db.session.add(link)
    db.session.commit()

    # Warm the cache
    redis_client.set(_cache_key(short_code), original_url, ex=CACHE_TTL)

    logger.info("link created", extra={"short_code": short_code, "user_id": user_id})
    result = link.to_dict()
    result["short_url"] = f"{BASE_URL}/{short_code}"
    return jsonify(result), 201


@links_bp.route("", methods=["GET"])
@jwt_required()
def list_links():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    pagination = (
        Link.query.filter_by(user_id=user_id)
        .order_by(Link.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    items = []
    for link in pagination.items:
        d = link.to_dict(include_stats=True)
        d["short_url"] = f"{BASE_URL}/{link.short_code}"
        items.append(d)

    return (
        jsonify(
            {
                "links": items,
                "total": pagination.total,
                "pages": pagination.pages,
                "page": page,
            }
        ),
        200,
    )


@links_bp.route("/<string:short_code>", methods=["DELETE"])
@jwt_required()
def delete_link(short_code: str):
    user_id = int(get_jwt_identity())
    link = Link.query.filter_by(short_code=short_code, user_id=user_id).first()
    if not link:
        return jsonify({"error": "link not found"}), 404

    redis_client.delete(_cache_key(short_code))
    db.session.delete(link)
    db.session.commit()

    logger.info("link deleted", extra={"short_code": short_code, "user_id": user_id})
    return jsonify({"message": "deleted"}), 200
