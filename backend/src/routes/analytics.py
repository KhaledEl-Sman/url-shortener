"""
Analytics routes: click stats per link
GET /api/analytics/<short_code>   summary + recent clicks
"""
import logging

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.extensions import redis_client
from src.models import Click, Link

analytics_bp = Blueprint("analytics", __name__)
logger = logging.getLogger(__name__)


@analytics_bp.route("/<string:short_code>", methods=["GET"])
@jwt_required()
def link_analytics(short_code: str):
    user_id = int(get_jwt_identity())
    link = Link.query.filter_by(short_code=short_code, user_id=user_id).first()
    if not link:
        return jsonify({"error": "link not found"}), 404

    # Fast counter from Redis (fallback to DB count)
    redis_total = redis_client.get(f"clicks:{short_code}:total")
    total_clicks = int(redis_total) if redis_total else link.click_count

    # Last 10 clicks from DB
    recent = (
        Click.query.filter_by(link_id=link.id)
        .order_by(Click.clicked_at.desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "short_code": short_code,
        "original_url": link.original_url,
        "total_clicks": total_clicks,
        "recent_clicks": [c.to_dict() for c in recent],
    }), 200
