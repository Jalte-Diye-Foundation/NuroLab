# File: nurolab/app_backend/models/database.py
# SQLAlchemy ORM models + engine/session setup for NuroLab.
#
# Tables: User, Baseline, Session, Prediction, Analytics

from __future__ import annotations

import datetime
from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session as ORMSession

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = STORAGE_DIR / "nurolab.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI's threaded workers
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── Tables ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    baselines = relationship("Baseline", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("SessionRecord", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.user_id"), nullable=False, index=True)

    alpha_mean = Column(Float, nullable=False)
    beta_mean = Column(Float, nullable=False)
    theta_mean = Column(Float, nullable=False)

    alpha_std = Column(Float, nullable=False)
    beta_std = Column(Float, nullable=False)
    theta_std = Column(Float, nullable=False)

    n_samples = Column(Integer, nullable=False)
    quality = Column(String(32), nullable=False, default="unknown")

    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="baselines")

    __table_args__ = (
        Index("ix_baselines_user_created", "user_id", "created_at"),
    )


class SessionRecord(Base):
    """A single saved measurement/session snapshot for a user."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.user_id"), nullable=False, index=True)

    alpha = Column(Float, nullable=False)
    beta = Column(Float, nullable=False)
    theta = Column(Float, nullable=False)

    deviation_score = Column(Float, nullable=False)
    risk_tier = Column(String(16), nullable=False)

    stress_prediction = Column(Float, nullable=True)
    attention_prediction = Column(Float, nullable=True)
    fatigue_prediction = Column(Float, nullable=True)

    timestamp = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_user_timestamp", "user_id", "timestamp"),
    )


class Prediction(Base):
    """Individual ML prediction events, kept separate from session snapshots
    so future model versions / audit trails can be tracked independently."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)

    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False, default="placeholder-v0")
    prediction_value = Column(Float, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_user_created", "user_id", "created_at"),
    )


class Analytics(Base):
    """Rolling aggregate stats per user (updated as sessions come in)."""

    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), ForeignKey("users.user_id"), nullable=False, index=True)

    avg_deviation_score = Column(Float, nullable=False, default=0.0)
    avg_stress = Column(Float, nullable=False, default=0.0)
    avg_attention = Column(Float, nullable=False, default=0.0)
    avg_fatigue = Column(Float, nullable=False, default=0.0)
    total_sessions = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="analytics")

    __table_args__ = (
        Index("ix_analytics_user", "user_id"),
    )


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session and ensures it's closed."""
    db: ORMSession = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_user(db: ORMSession, user_id: str) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        user = User(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
