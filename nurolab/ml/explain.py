# File: nurolab/ml/explain.py
# XAI — Explainable AI Contributing Factors
#
# Converts raw z-score vectors into human-readable strings
# that the app can display to the user.

import numpy as np


def explain_prediction(
    z_scores,
    feature_names: list,
    top_k: int = 3,
) -> list:
    """
    Returns human-readable descriptions of the top contributing features.

    Args:
        z_scores:      list or array of per-feature z-scores
        feature_names: list of feature name strings (same order)
        top_k:         how many top features to include

    Returns:
        List of strings, e.g.:
          ["Fp1 alpha DE is elevated (+2.3σ from baseline)",
           "F4 theta activity is reduced (-1.8σ from baseline)"]
    """
    z = np.array(z_scores)
    top_idx = np.argsort(np.abs(z))[::-1][:top_k]
    out = []
    for idx in top_idx:
        name = feature_names[idx].replace("_", " ")
        direction = "elevated" if z[idx] > 0 else "reduced"
        out.append(f"{name} is {direction} ({z[idx]:+.1f}σ from baseline)")
    return out


def risk_tier_from_mahalanobis(mahal_dist: float) -> int:
    """
    Map a Mahalanobis distance to a 0–3 risk tier.

    Thresholds are heuristic — tune after calibrating on your population.
      0: baseline (< 2σ)
      1: mild deviation (2–4σ)
      2: moderate deviation (4–7σ)
      3: significant deviation (> 7σ)
    """
    if mahal_dist < 2.0:
        return 0
    elif mahal_dist < 4.0:
        return 1
    elif mahal_dist < 7.0:
        return 2
    else:
        return 3
