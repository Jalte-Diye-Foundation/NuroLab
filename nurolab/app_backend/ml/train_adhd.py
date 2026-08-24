# File: nurolab/ml/train_adhd.py
#
# Trains an ADHD classifier with subject-level k-fold cross-validation,
# on the 121-subject EEG dataset (61 ADHD, 60 Control), 128Hz, 19 channels.
#
# Correctness requirements (verified against live serving code):
# 1. Feature computation uses compute_full_channel_features() from
#    app_backend/eeg/features.py — matches exactly what the live
#    /clinical/predict/adhd endpoint computes at inference time.
# 2. No filtering before feature extraction — matches how server.py's
#    existing clinical endpoints call build_feature_vector() on raw
#    samples directly.
#
# DATA LEAKAGE PREVENTION — two layers:
# 1. StratifiedGroupKFold with subject_id as the group — guarantees
#    every window from a given subject stays entirely within one fold,
#    never split across train/test within any single fold.
# 2. Non-overlapping windows (5s window, 5s stride) — avoids windows
#    from the same subject being near-duplicates of each other even
#    within a fold.
#
# This version replaces the earlier single 75/25 split with 5-fold CV,
# reporting mean +/- std accuracy — a more robust estimate than any one
# split, which could be lucky or unlucky.

from __future__ import annotations

import joblib
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

from nurolab.datasources.adhd_loader import load_subjects
from nurolab.app_backend.eeg.features import compute_full_channel_features

DATA_PATH = "nurolab/data/adhd_eeg/adhdata.csv"
WINDOW_SEC = 5.0
STRIDE_SEC = 5.0
N_FOLDS = 5
MODEL_OUT_PATH = "nurolab/app_backend/clinical_models/nurolab_adhd_svm.pkl"

CHANNEL_NAMES = [
    "FP1", "FP2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2",
    "F7", "F8", "T7", "T8", "P7", "P8", "FZ", "CZ", "PZ",
]


def windows_for_subject(data: np.ndarray, fs: float) -> list[np.ndarray]:
    win_samples = int(WINDOW_SEC * fs)
    step_samples = int(STRIDE_SEC * fs)
    windows = []
    start = 0
    while start + win_samples <= len(data):
        windows.append(data[start:start + win_samples, :])
        start += step_samples
    return windows


def build_feature_vector_and_names(window: np.ndarray, fs: float) -> tuple[np.ndarray, list[str]]:
    values, names = [], []
    for ch_idx, ch_name in enumerate(CHANNEL_NAMES):
        channel_signal = window[:, ch_idx]
        metrics = compute_full_channel_features(channel_signal, fs)
        for metric_name, value in metrics.items():
            values.append(value)
            names.append(f"{ch_name}_{metric_name}")
    return np.array(values), names


def make_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svc", CalibratedClassifierCV(
            SVC(kernel="rbf", class_weight="balanced", random_state=42),
            method="sigmoid",
        )),
    ])


def main():
    print(f"Loading subjects from {DATA_PATH} ...")
    subjects = load_subjects(DATA_PATH)
    print(f"Loaded {len(subjects)} subjects "
          f"({sum(1 for s in subjects if s['label']=='ADHD')} ADHD, "
          f"{sum(1 for s in subjects if s['label']=='Control')} Control)\n")

    print("Extracting features for ALL subjects (using the same function the live server uses)...")
    X, y, groups = [], [], []
    feature_names = None
    for s in subjects:
        windows = windows_for_subject(s["data"], s["fs"])
        for w in windows:
            fv, names = build_feature_vector_and_names(w, s["fs"])
            if feature_names is None:
                feature_names = names
            else:
                assert names == feature_names, "Feature name order mismatch between windows!"
            X.append(fv)
            y.append(1 if s["label"] == "ADHD" else 0)
            groups.append(s["subject_id"])  # every window tagged with its subject

    X = np.array(X)
    y = np.array(y)
    groups = np.array(groups)
    print(f"Total: {len(X)} windows across {len(subjects)} subjects, {X.shape[1]} features each\n")

    # ---- Subject-level k-fold CV ----
    print(f"Running {N_FOLDS}-fold subject-level cross-validation...")
    print("(StratifiedGroupKFold — every subject's windows stay entirely within one fold,")
    print(" never split across train/test within any given fold)\n")

    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=42)
    fold_accuracies = []

    for fold_idx, (train_idx, test_idx) in enumerate(sgkf.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Sanity check: confirm no subject leaks across train/test in this fold.
        train_subjects = set(groups[train_idx])
        test_subjects = set(groups[test_idx])
        overlap = train_subjects & test_subjects
        assert not overlap, f"Fold {fold_idx}: subject leakage detected! {overlap}"

        pipeline = make_pipeline()
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        fold_accuracies.append(acc)

        print(f"Fold {fold_idx + 1}/{N_FOLDS}: accuracy={acc:.4f} "
              f"({len(train_subjects)} train subjects, {len(test_subjects)} test subjects, "
              f"0 overlap confirmed)")

    mean_acc = float(np.mean(fold_accuracies))
    std_acc = float(np.std(fold_accuracies))

    print("\n" + "=" * 60)
    print(f"Cross-validated accuracy: {mean_acc:.4f} +/- {std_acc:.4f} (across {N_FOLDS} folds)")
    print(f"Per-fold: {[round(a, 4) for a in fold_accuracies]}")
    print("=" * 60)

    # ---- Train the FINAL model on ALL data for actual deployment ----
    # CV tells us the honest expected generalization performance; the
    # shipped model itself uses all available data for best real-world
    # performance, standard practice.
    print("\nTraining final model on ALL 121 subjects for deployment...")
    final_pipeline = make_pipeline()
    final_pipeline.fit(X, y)

    joblib.dump({
        "pipeline": final_pipeline,
        "feature_names": feature_names,
        "condition": "adhd",
        "cv_accuracy": mean_acc,
        "cv_std": std_acc,
        "cv_per_fold": [round(a, 4) for a in fold_accuracies],
        "label_map": {0: "control", 1: "adhd"},
    }, MODEL_OUT_PATH)
    print(f"Saved final model to {MODEL_OUT_PATH}")
    print(f"\nReported accuracy going forward: {mean_acc:.4f} +/- {std_acc:.4f} "
          f"(honest, cross-validated — not a single lucky/unlucky split)")


if __name__ == "__main__":
    main()
