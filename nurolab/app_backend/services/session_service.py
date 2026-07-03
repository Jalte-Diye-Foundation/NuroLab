# File: nurolab/app_backend/services/session_service.py
# Save session snapshots and query paginated/sorted history.

from __future__ import annotations

from typing import Literal

from sqlalchemy.orm import Session as ORMSession

from nurolab.app_backend.models.database import Analytics, SessionRecord, get_or_create_user


def save_session(
    db: ORMSession,
    user_id: str,
    alpha: float,
    beta: float,
    theta: float,
    deviation_score: float,
    risk_tier: str,
    stress_prediction: float | None = None,
    attention_prediction: float | None = None,
    fatigue_prediction: float | None = None,
) -> SessionRecord:
    get_or_create_user(db, user_id)

    record = SessionRecord(
        user_id=user_id,
        alpha=alpha,
        beta=beta,
        theta=theta,
        deviation_score=deviation_score,
        risk_tier=risk_tier,
        stress_prediction=stress_prediction,
        attention_prediction=attention_prediction,
        fatigue_prediction=fatigue_prediction,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    _update_analytics(db, user_id)
    return record


def _update_analytics(db: ORMSession, user_id: str) -> None:
    """Recompute rolling averages for the user's Analytics row."""
    sessions = db.query(SessionRecord).filter(SessionRecord.user_id == user_id).all()
    if not sessions:
        return

    n = len(sessions)
    avg_deviation = sum(s.deviation_score for s in sessions) / n
    avg_stress = sum(s.stress_prediction or 0.0 for s in sessions) / n
    avg_attention = sum(s.attention_prediction or 0.0 for s in sessions) / n
    avg_fatigue = sum(s.fatigue_prediction or 0.0 for s in sessions) / n

    analytics = db.query(Analytics).filter(Analytics.user_id == user_id).first()
    if analytics is None:
        analytics = Analytics(user_id=user_id)
        db.add(analytics)

    analytics.avg_deviation_score = avg_deviation
    analytics.avg_stress = avg_stress
    analytics.avg_attention = avg_attention
    analytics.avg_fatigue = avg_fatigue
    analytics.total_sessions = n

    db.commit()


def get_history(
    db: ORMSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    sort: Literal["asc", "desc"] = "desc",
) -> list[SessionRecord]:
    query = db.query(SessionRecord).filter(SessionRecord.user_id == user_id)

    if sort == "asc":
        query = query.order_by(SessionRecord.timestamp.asc())
    else:
        query = query.order_by(SessionRecord.timestamp.desc())

    return query.offset(offset).limit(limit).all()
