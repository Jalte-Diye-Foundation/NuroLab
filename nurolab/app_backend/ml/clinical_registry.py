# File: nurolab/app_backend/ml/clinical_registry.py
# Loads the clinical multi-channel SVM models (epilepsy, depression).
#
# These are a DIFFERENT format from the lightweight stress/attention/fatigue
# ModelRegistry in model_registry.py:
#   - Saved as a dict: {"pipeline": sklearn Pipeline, "feature_names": [...],
#     "condition": str, "cv_accuracy": float, "cv_std": float,
#     "cv_per_fold": [...], "label_map": {...} (epilepsy only)}
#   - The pipeline is (SelectFpr -> StandardScaler -> CalibratedClassifierCV(SVC))
#   - feature_names defines the EXACT expected input feature order, keyed as
#     "{CHANNEL}_{metric}" e.g. "FP1_delta_DE", "EEG1_hjorth_activity".
#   - epilepsy is 3-class: {0: normal, 1: interictal, 2: seizure}
#   - depression is 2-class: {"control", "depressed"}
#
# IMPORTANT — data quality caveat (surfaced in /clinical/models/status too):
#   The depression model's own recorded cross-validation accuracy is ~38%
#   (fold range 10%-58%) on only 7 subjects — essentially unreliable for a
#   binary task. The epilepsy model's recorded cv_accuracy is ~89%, which is
#   more usable but should still be validated against your own held-out data
#   before any real decision-making relies on it. Neither model is a
#   substitute for clinical diagnosis.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from nurolab.app_backend.eeg.features import compute_full_channel_features

logger = logging.getLogger("nurolab.ml.clinical")


class ClinicalModel:
    """Wraps one loaded clinical model bundle (pipeline + metadata)."""

    def __init__(self, path: Path, bundle: dict):
        self.path = path
        self.pipeline = bundle["pipeline"]
        self.feature_names: list[str] = bundle["feature_names"]
        self.condition: str = bundle.get("condition", path.stem)
        self.cv_accuracy: float = bundle.get("cv_accuracy")
        self.cv_std: float = bundle.get("cv_std")
        self.label_map: Optional[dict] = bundle.get("label_map")  # epilepsy has this; depression uses pipeline.classes_

        # Parse "{CHANNEL}_{metric}" -> (channel, metric) once, up front.
        self._required: list[tuple[str, str, str]] = []  # (full_name, channel, metric)
        for name in self.feature_names:
            channel, metric = name.split("_", 1)
            self._required.append((name, channel, metric))

        self.required_channels: list[str] = sorted({c for _, c, _ in self._required})

    def build_feature_vector(
        self, channel_data: dict[str, np.ndarray], fs: float
    ) -> tuple[np.ndarray, list[str]]:
        """Builds the exact-order feature vector this model expects.

        Args:
            channel_data: {channel_name: 1D sample array}
            fs: sampling rate of the provided samples

        Returns:
            (feature_vector, missing_channels) — missing channels are filled
            with 0.0 in the vector (so the call doesn't hard-fail), but are
            reported back so the caller can warn the user reliability is
            degraded.
        """
        # Compute full per-channel feature dict only for channels we have.
        computed: dict[str, dict[str, float]] = {}
        missing_channels = [c for c in self.required_channels if c not in channel_data]

        for ch in self.required_channels:
            if ch in channel_data:
                computed[ch] = compute_full_channel_features(np.asarray(channel_data[ch], dtype=float), fs)

        vector = np.zeros(len(self._required), dtype=float)
        for i, (full_name, channel, metric) in enumerate(self._required):
            if channel in computed and metric in computed[channel]:
                vector[i] = computed[channel][metric]
            # else: leave as 0.0 (missing channel) — already tracked above

        return vector, missing_channels

    def predict(self, feature_vector: np.ndarray) -> dict:
        """Runs the pipeline and returns label + per-class probabilities."""
        X = feature_vector.reshape(1, -1)
        proba = self.pipeline.predict_proba(X)[0]
        classes = self.pipeline.classes_

        proba_by_class = {}
        for cls, p in zip(classes, proba):
            label = self.label_map[cls] if self.label_map and cls in self.label_map else str(cls)
            proba_by_class[label] = float(p)

        best_idx = int(np.argmax(proba))
        best_class = classes[best_idx]
        predicted_label = self.label_map[best_class] if self.label_map and best_class in self.label_map else str(best_class)

        return {
            "predicted_label": predicted_label,
            "probabilities": proba_by_class,
        }


class ClinicalModelRegistry:
    """Loads whichever clinical .pkl bundles exist under a given directory."""

    def __init__(self, model_paths: dict[str, Path]):
        self.models: dict[str, ClinicalModel] = {}
        for name, path in model_paths.items():
            if not path.exists():
                logger.info("Clinical model '%s' not found at %s — endpoint will 503.", name, path)
                continue
            try:
                import joblib
                bundle = joblib.load(path)
                self.models[name] = ClinicalModel(path, bundle)
                logger.info(
                    "Loaded clinical model '%s' (condition=%s, cv_accuracy=%.3f, features=%d)",
                    name, self.models[name].condition, self.models[name].cv_accuracy or -1,
                    len(self.models[name].feature_names),
                )
            except Exception as exc:
                logger.error("Failed to load clinical model '%s' from %s: %s", name, path, exc)

    def get(self, name: str) -> Optional[ClinicalModel]:
        return self.models.get(name)

    def loaded_names(self) -> list[str]:
        return list(self.models.keys())
