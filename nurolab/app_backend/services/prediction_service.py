# File: nurolab/app_backend/services/prediction_service.py
# Prediction functions for stress / attention / fatigue.
#
# Each function tries a real trained model first (via ModelRegistry, if one
# was loaded successfully), and falls back to a deterministic heuristic if
# no trained model is available for that condition. This means the API
# behaves identically whether you have 0, 1, 2, or all 3 real models loaded.

from __future__ import annotations

from typing import Optional

import numpy as np

from nurolab.app_backend.ml.model_registry import ModelRegistry


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def _heuristic_stress(alpha_de: float, beta_de: float, theta_de: float) -> float:
    """Fallback heuristic: stress correlates with elevated beta relative to alpha."""
    score = (beta_de - alpha_de) * 1.5
    return round(_sigmoid(score), 4)


def _heuristic_attention(alpha_de: float, beta_de: float, theta_de: float) -> float:
    """Fallback heuristic: attention correlates with beta activity, suppressed theta."""
    score = (beta_de - theta_de) * 1.2
    return round(_sigmoid(score), 4)


def _heuristic_fatigue(alpha_de: float, beta_de: float, theta_de: float) -> float:
    """Fallback heuristic: fatigue correlates with elevated theta/alpha vs beta."""
    score = (theta_de + alpha_de - beta_de) * 1.0
    return round(_sigmoid(score), 4)


def predict_stress(alpha_de: float, beta_de: float, theta_de: float, registry: Optional[ModelRegistry] = None) -> float:
    if registry is not None:
        result = registry.predict("stress", alpha_de, beta_de, theta_de)
        if result is not None:
            return round(result, 4)
    return _heuristic_stress(alpha_de, beta_de, theta_de)


def predict_attention(alpha_de: float, beta_de: float, theta_de: float, registry: Optional[ModelRegistry] = None) -> float:
    if registry is not None:
        result = registry.predict("attention", alpha_de, beta_de, theta_de)
        if result is not None:
            return round(result, 4)
    return _heuristic_attention(alpha_de, beta_de, theta_de)


def predict_fatigue(alpha_de: float, beta_de: float, theta_de: float, registry: Optional[ModelRegistry] = None) -> float:
    if registry is not None:
        result = registry.predict("fatigue", alpha_de, beta_de, theta_de)
        if result is not None:
            return round(result, 4)
    return _heuristic_fatigue(alpha_de, beta_de, theta_de)


def predict_all(alpha_de: float, beta_de: float, theta_de: float, registry: Optional[ModelRegistry] = None) -> dict[str, float]:
    """Run stress/attention/fatigue prediction, using real models where loaded
    and heuristic fallback otherwise."""
    return {
        "stress_prediction": predict_stress(alpha_de, beta_de, theta_de, registry),
        "attention_prediction": predict_attention(alpha_de, beta_de, theta_de, registry),
        "fatigue_prediction": predict_fatigue(alpha_de, beta_de, theta_de, registry),
    }
