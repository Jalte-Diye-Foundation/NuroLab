# File: nurolab/app_backend/services/analytics_service.py
# Differential entropy, deviation-from-baseline, and risk-tier computation.

from __future__ import annotations

import numpy as np

from nurolab.app_backend.eeg.features import compute_multichannel_de
from nurolab.app_backend.models.database import Baseline

# Deviation-score thresholds (see task spec):
#   <20        -> LOW
#   20-50      -> MODERATE
#   >50        -> HIGH
LOW_THRESHOLD = 20.0
HIGH_THRESHOLD = 50.0


def compute_DE(data: np.ndarray, fs: float) -> dict:
    """Compute alpha/beta/theta differential entropy for a raw EEG window.

    `data` should already be preprocessed (filtered/normalized).
    Returns a dict with alpha_de, beta_de, theta_de (+ raw band powers).
    """
    return compute_multichannel_de(data, fs)


def compute_deviation(current: dict, baseline: Baseline) -> float:
    """Weighted z-score-style deviation of current alpha/beta/theta from baseline.

    Returns a single scalar deviation score, scaled to roughly a 0-100+ range
    so it lines up with the LOW/MODERATE/HIGH thresholds.
    """
    alpha_z = (current["alpha"] - baseline.alpha_mean) / (baseline.alpha_std or 1e-6)
    beta_z = (current["beta"] - baseline.beta_mean) / (baseline.beta_std or 1e-6)
    theta_z = (current["theta"] - baseline.theta_mean) / (baseline.theta_std or 1e-6)

    # Combine via Euclidean norm of z-scores, then scale into a 0-100-ish range.
    # A combined z-norm of ~3 (fairly extreme deviation across all 3 bands)
    # maps to a deviation score of 100.
    z_norm = float(np.sqrt(alpha_z**2 + beta_z**2 + theta_z**2))
    deviation_score = min(z_norm / 3.0, 1.0) * 100.0
    return round(deviation_score, 2)


def compute_risk(deviation_score: float) -> str:
    """Map a deviation score to a risk tier string."""
    if deviation_score < LOW_THRESHOLD:
        return "low"
    if deviation_score <= HIGH_THRESHOLD:
        return "moderate"
    return "high"
