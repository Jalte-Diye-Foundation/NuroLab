# File: nurolab/ml/model_registry.py
# Unified Model Registry
#
# Loads all trained condition models and runs unified inference.
# Supports both the new pipeline-based artifacts (post-leakage-fix) and
# the older model/scaler/anova_mask format for backward compatibility.

import joblib
import numpy as np
from pathlib import Path
from nurolab.processing.features import extract_feature_vector

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ModelRegistry:
    """
    Loads all trained condition models and runs unified inference.

    Usage:
        registry = ModelRegistry({
            'depression': 'models/nurolab_depression_svm.pkl',
            'epilepsy':   'models/nurolab_epilepsy_svm.pkl',
        })
        results = registry.predict_all(filtered_window, fs=512.0)
    """

    def __init__(self, model_paths: dict):
        self.models = {}
        for condition, path in model_paths.items():
            model_path = Path(path)
            if not model_path.is_absolute():
                model_path = PROJECT_ROOT / model_path

            if model_path.exists():
                artifact = joblib.load(model_path)
                self.models[condition] = artifact
                acc = artifact.get("cv_accuracy")
                acc_str = f"{acc:.3f}" if acc is not None else "?"
                print(f"[ModelRegistry] Loaded '{condition}' from {model_path} (CV acc: {acc_str})")
            else:
                print(f"[ModelRegistry] WARNING: model not found at {model_path} — "
                      f"'{condition}' predictions will be skipped.")

    def predict_all(self, window: np.ndarray, fs: float) -> dict:
        fv = extract_feature_vector(window, fs)
        results = {}

        for condition, artifact in self.models.items():
            try:
                if "pipeline" in artifact:
                    # New format: single sklearn Pipeline handles
                    # selection + scaling + classification together.
                    pipe = artifact["pipeline"]
                    x = fv.reshape(1, -1)
                    label = pipe.predict(x)[0]
                    proba = pipe.predict_proba(x)[0]
                    results[condition] = {
                        "label":      str(label),
                        "confidence": float(np.max(proba)),
                    }
                else:
                    # Legacy format
                    mask = artifact.get("anova_mask")
                    x = fv[mask] if mask is not None else fv
                    x_norm = artifact["scaler"].transform(x.reshape(1, -1))
                    label = artifact["model"].predict(x_norm)[0]
                    proba = artifact["model"].predict_proba(x_norm)[0]
                    results[condition] = {
                        "label":      str(label),
                        "confidence": float(np.max(proba)),
                    }
            except Exception as e:
                results[condition] = {"error": str(e)}

        return results

    def is_ready(self, condition: str) -> bool:
        return condition in self.models
