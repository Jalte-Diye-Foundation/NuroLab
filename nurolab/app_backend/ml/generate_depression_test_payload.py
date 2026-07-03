# File: nurolab/app_backend/ml/generate_depression_test_payload.py
# Generates a synthetic full-montage (all 66 required channels) JSON payload
# so you can test POST /clinical/predict/depression with ZERO missing
# channels — i.e. exercising the model exactly as it expects to be called,
# without waiting for real 66-channel hardware.
#
# The channel LIST is read directly from the loaded model's feature_names,
# so it always matches whatever nurolab_depression_svm.pkl actually expects
# — no hardcoded channel list to go stale.
#
# Run with (from the project root, i.e. the folder containing nurolab/):
#   python -m nurolab.app_backend.ml.generate_depression_test_payload > /tmp/depression_full.json
#   curl -X POST http://127.0.0.1:8000/clinical/predict/depression \
#     -H "Content-Type: application/json" -d @/tmp/depression_full.json

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root on path

from nurolab.app_backend.ml.clinical_registry import ClinicalModelRegistry

CLINICAL_MODELS_DIR = Path(__file__).resolve().parent.parent / "clinical_models"


def main():
    registry = ClinicalModelRegistry({
        "depression": CLINICAL_MODELS_DIR / "nurolab_depression_svm.pkl",
    })
    model = registry.get("depression")
    if model is None:
        print(
            "depression model not found at "
            f"{CLINICAL_MODELS_DIR / 'nurolab_depression_svm.pkl'} — nothing to generate.",
            file=sys.stderr,
        )
        sys.exit(1)

    fs = 256.0
    n_samples = int(fs * 2)  # 2-second window, matches the rest of the pipeline
    rng = np.random.default_rng(0)

    channels = {
        ch: rng.normal(0, 1, n_samples).round(4).tolist()
        for ch in model.required_channels
    }

    payload = {"channels": channels, "fs": fs}
    print(json.dumps(payload))
    print(
        f"Generated {len(channels)} synthetic channels -> stderr for confirmation",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
