# File: nurolab/app_backend/ml/model_registry.py
# Loads real trained ML models (scikit-learn-style .pkl files) for
# stress / attention / fatigue prediction, with automatic fallback to the
# heuristic placeholder functions if a model file is missing or fails to load.
#
# Expected model contract:
#   - Trained with joblib.dump(model, "stress_model.pkl") (or pickle)
#   - Exposes .predict_proba(X) where X is shape (n_samples, n_features)
#     and predict_proba returns shape (n_samples, 2) -> [:, 1] is the
#     "positive class" probability (e.g. probability of "stressed").
#   - Feature order MUST be [alpha_de, beta_de, theta_de] unless you change
#     FEATURE_NAMES below and retrain accordingly.
#
# If your model doesn't follow sklearn's predict_proba convention (e.g. it's
# a raw PyTorch/TensorFlow model, or predict() returns [0,1] scores
# directly), see the `_score()` method — that's the one place to adapt.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger("nurolab.ml")

FEATURE_NAMES = ["alpha_de", "beta_de", "theta_de"]


class LoadedModel:
    """Wraps a single loaded model + metadata."""

    def __init__(self, name: str, path: Path, model):
        self.name = name
        self.path = path
        self.model = model

    def score(self, features: np.ndarray) -> float:
        """Return a single probability-like float in [0, 1] for one feature row.

        features: 1D array matching FEATURE_NAMES order.
        """
        X = features.reshape(1, -1)

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
            # Standard sklearn binary classifier: [:, 1] is P(positive class)
            value = float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        elif hasattr(self.model, "predict"):
            # Regressor or model without predict_proba: assume predict()
            # already returns a [0,1]-ish score.
            value = float(np.ravel(self.model.predict(X))[0])
        else:
            raise TypeError(
                f"Model '{self.name}' has neither predict_proba nor predict; "
                "adapt LoadedModel.score() for your model type."
            )

        return float(np.clip(value, 0.0, 1.0))


class ModelRegistry:
    """Loads whichever of stress/attention/fatigue .pkl files exist.

    Missing files are skipped (not an error) — server.py falls back to the
    heuristic prediction_service functions for any model that isn't loaded,
    so the API keeps working even with 0, 1, 2, or 3 models present.
    """

    def __init__(self, model_paths: dict[str, Path]):
        self.models: dict[str, LoadedModel] = {}
        self._load_all(model_paths)

    def _load_all(self, model_paths: dict[str, Path]) -> None:
        for name, path in model_paths.items():
            if not path.exists():
                logger.info("Model '%s' not found at %s — will use heuristic fallback.", name, path)
                continue
            try:
                import joblib  # local import: joblib is an extra dependency only needed here
                model = joblib.load(path)
                self.models[name] = LoadedModel(name, path, model)
                logger.info("Loaded model '%s' from %s", name, path)
            except Exception as exc:
                logger.error("Failed to load model '%s' from %s: %s", name, path, exc)

    def has(self, name: str) -> bool:
        return name in self.models

    def predict(self, name: str, alpha_de: float, beta_de: float, theta_de: float) -> Optional[float]:
        """Returns a probability in [0,1], or None if this model isn't loaded
        (caller should fall back to the heuristic in that case)."""
        if name not in self.models:
            return None
        features = np.array([alpha_de, beta_de, theta_de], dtype=float)
        try:
            return self.models[name].score(features)
        except Exception as exc:
            logger.error("Model '%s' failed during prediction: %s — falling back to heuristic.", name, exc)
            return None

    def loaded_names(self) -> list[str]:
        return list(self.models.keys())
