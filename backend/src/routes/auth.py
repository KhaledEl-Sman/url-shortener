"""
Auth routes: /api/auth/register  /api/auth/login  /api/auth/logout  /api/auth/me
"""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from src.extensions import db, limiter, redis_client
from src.models import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

BLOCKLIST_PREFIX = "jwt_blocklist:"
TOKEN_TTL = 60 * 60 * 24  # 24 h


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    logger.info("user registered", extra={"user_id": user.id, "email": email})
    return jsonify({"access_token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    logger.info("user logged in", extra={"user_id": user.id})
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    redis_client.set(f"{BLOCKLIST_PREFIX}{jti}", "1", ex=TOKEN_TTL)
    logger.info("user logged out", extra={"user_id": get_jwt_identity()})
    return jsonify({"message": "logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
