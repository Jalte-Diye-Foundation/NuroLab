# File: nurolab/app_backend/ml/train_example_models.py
# Generates EXAMPLE trained models so you can test the real-model integration
# end-to-end before your actually-trained models are ready.
#
# These are trained on synthetic data with made-up labels — they are NOT
# scientifically meaningful. They exist purely to prove the loading/serving
# pipeline works. Replace the .pkl files this produces with your real
# trained models (same filenames, same folder) when they're ready.
#
# Run with (from the project root, i.e. the folder containing nurolab/):
#   python -m nurolab.app_backend.ml.train_example_models

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "models_store"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_synthetic_dataset(n_samples: int = 2000, seed: int = 42):
    rng = np.random.default_rng(seed)
    alpha_de = rng.normal(0, 1, n_samples)
    beta_de = rng.normal(0, 1, n_samples)
    theta_de = rng.normal(0, 1, n_samples)
    X = np.column_stack([alpha_de, beta_de, theta_de])
    return X


def train_and_save(name: str, label_fn, X: np.ndarray) -> None:
    y = label_fn(X)
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=0)
    model.fit(X, y)

    out_path = OUTPUT_DIR / f"{name}_model.pkl"
    joblib.dump(model, out_path)
    print(f"Saved example '{name}' model -> {out_path}")


def main():
    X = make_synthetic_dataset()

    # Made-up label rules mirroring the heuristic logic, just so the example
    # models produce sane-looking (not random) outputs.
    train_and_save("stress", lambda X: (X[:, 1] - X[:, 0] > 0).astype(int), X)      # beta > alpha
    train_and_save("attention", lambda X: (X[:, 1] - X[:, 2] > 0).astype(int), X)   # beta > theta
    train_and_save("fatigue", lambda X: (X[:, 2] + X[:, 0] - X[:, 1] > 0).astype(int), X)  # theta+alpha > beta

    print("\nDone. Restart the server to pick up these models, then check:")
    print("  GET /models/status")


if __name__ == "__main__":
    main()
