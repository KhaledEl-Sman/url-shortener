"""
SQLAlchemy models: User, Link, Click
"""

import datetime

import bcrypt

from src.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    links = db.relationship(
        "Link", back_populates="owner", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


class Link(db.Model):
    __tablename__ = "links"

    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    owner = db.relationship("User", back_populates="links")
    clicks = db.relationship(
        "Click", back_populates="link", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def click_count(self):
        return self.clicks.count()

    def to_dict(self, include_stats=False):
        data = {
            "id": self.id,
            "short_code": self.short_code,
            "original_url": self.original_url,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }
        if include_stats:
            data["click_count"] = self.click_count
        return data


class Click(db.Model):
    __tablename__ = "clicks"

    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(
        db.Integer, db.ForeignKey("links.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clicked_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6-safe length
    user_agent = db.Column(db.String(512), nullable=True)
    referer = db.Column(db.String(1024), nullable=True)

    link = db.relationship("Link", back_populates="clicks")

    def to_dict(self):
        return {
            "id": self.id,
            "link_id": self.link_id,
            "clicked_at": self.clicked_at.isoformat(),
            "ip_address": self.ip_address,
            "referer": self.referer,
        }
