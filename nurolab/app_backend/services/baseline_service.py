# File: nurolab/app_backend/services/baseline_service.py
# Baseline computation + persistence.

from __future__ import annotations

import numpy as np
from sqlalchemy.orm import Session as ORMSession

from nurolab.app_backend.models.database import Baseline, get_or_create_user


def calculate_statistics(alpha: list[float], beta: list[float], theta: list[float]) -> dict:
    """Compute mean/std/sample-count statistics for a baseline calibration recording."""
    a = np.asarray(alpha, dtype=float)
    b = np.asarray(beta, dtype=float)
    t = np.asarray(theta, dtype=float)

    n_samples = int(len(a))
    quality = _quality_from_sample_count(n_samples)

    return {
        "alpha_mean": float(np.mean(a)),
        "beta_mean": float(np.mean(b)),
        "theta_mean": float(np.mean(t)),
        "alpha_std": float(np.std(a)) or 1e-6,
        "beta_std": float(np.std(b)) or 1e-6,
        "theta_std": float(np.std(t)) or 1e-6,
        "n_samples": n_samples,
        "quality": quality,
    }


def _quality_from_sample_count(n_samples: int) -> str:
    if n_samples >= 200:
        return "good"
    if n_samples >= 50:
        return "fair"
    return "poor"


def build_baseline(
    db: ORMSession,
    user_id: str,
    alpha: list[float],
    beta: list[float],
    theta: list[float],
    feature_vectors: list[list[float]] | None = None,
    feature_names: list[str] | None = None,
) -> Baseline:
    """Compute stats and persist a new Baseline row for the user.

    feature_vectors/feature_names are optional — existing callers that only
    pass alpha/beta/theta keep working exactly as before. When provided
    (full feature vectors from calibration windows, matching what
    extract_feature_vector() produces), they're stored raw so a
    DeviationEngine can be rebuilt from them later — see
    processing/deviation_engine.py.
    """
    get_or_create_user(db, user_id)
    stats = calculate_statistics(alpha, beta, theta)

    baseline = Baseline(
        user_id=user_id,
        alpha_mean=stats["alpha_mean"],
        beta_mean=stats["beta_mean"],
        theta_mean=stats["theta_mean"],
        alpha_std=stats["alpha_std"],
        beta_std=stats["beta_std"],
        theta_std=stats["theta_std"],
        n_samples=stats["n_samples"],
        quality=stats["quality"],
        feature_vectors=feature_vectors,
        feature_names=feature_names,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return baseline


def get_latest_baseline(db: ORMSession, user_id: str) -> Baseline | None:
    return (
        db.query(Baseline)
        .filter(Baseline.user_id == user_id)
        .order_by(Baseline.created_at.desc())
        .first()
    )


def has_full_feature_baseline(baseline: Baseline | None) -> bool:
    """True if this baseline has enough data to build a DeviationEngine
    (not just the legacy 3-scalar alpha/beta/theta stats)."""
    return (
        baseline is not None
        and baseline.feature_vectors is not None
        and len(baseline.feature_vectors) >= 2  # need >=2 rows for a covariance matrix
    )
