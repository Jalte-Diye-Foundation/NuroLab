# File: nurolab/ml/train_adhd.py
#
# Trains an ADHD classifier on the 121-subject EEG dataset (61 ADHD,
# 60 Control), 128Hz, 19 channels.
#
# TWO correctness requirements verified against the actual live serving
# code (ClinicalModelRegistry / server.py) before writing this:
#
# 1. Feature computation MUST use compute_full_channel_features() from
#    app_backend/eeg/features.py — NOT processing/features.py's
#    extract_feature_vector(). These two files define EEG bands with
#    slightly different frequency ranges; training on one and serving
#    with the other would silently feed the model different feature
#    values than it learned on.
#
# 2. NO filtering is applied before feature extraction — confirmed by
#    reading server.py's existing /clinical/predict/epilepsy and
#    /clinical/predict/depression endpoints, which pass raw samples
#    directly into build_feature_vector() with no bandpass/notch step.
#    Training matches this exactly, for consistency with how the
#    existing clinical models were built and how this will actually run.
#
# DATA LEAKAGE PREVENTION: split happens at the SUBJECT level, not the
# window level — entire subjects go to train or test, never split
# across both, since windows from the same subject are highly
# correlated.
#
# HONESTY NOTE: this reports a single subject-level train/test split
# accuracy, not k-fold cross-validated. A proper next step would be
# repeated subject-level CV for a more robust estimate — flagged here
# rather than silently presented as more rigorous than it is.

from __future__ import annotations

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

from nurolab.datasources.adhd_loader import load_subjects
from nurolab.app_backend.eeg.features import compute_full_channel_features

DATA_PATH = "nurolab/data/adhd_eeg/adhdata.csv"
WINDOW_SEC = 5.0
STRIDE_SEC = 5.0  # non-overlapping — avoids correlated windows even within one subject
MODEL_OUT_PATH = "nurolab/app_backend/clinical_models/nurolab_adhd_svm.pkl"

# Uppercase, matching the convention shown in ClinicalModel's docstring
# ("FP1_delta_DE") — must match whatever channel names get passed in
# channel_data at inference time.
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
    """window shape: (n_samples, 19) — one column per channel, in
    CHANNEL_NAMES order. Builds a flat feature vector using the SAME
    per-channel function the live clinical registry uses at inference.
    """
    values = []
    names = []
    for ch_idx, ch_name in enumerate(CHANNEL_NAMES):
        channel_signal = window[:, ch_idx]
        metrics = compute_full_channel_features(channel_signal, fs)
        for metric_name, value in metrics.items():
            values.append(value)
            names.append(f"{ch_name}_{metric_name}")
    return np.array(values), names


def main():
    print(f"Loading subjects from {DATA_PATH} ...")
    subjects = load_subjects(DATA_PATH)
    print(f"Loaded {len(subjects)} subjects "
          f"({sum(1 for s in subjects if s['label']=='ADHD')} ADHD, "
          f"{sum(1 for s in subjects if s['label']=='Control')} Control)\n")

    subject_ids = [s["subject_id"] for s in subjects]
    labels = [s["label"] for s in subjects]

    train_ids, test_ids = train_test_split(
        subject_ids, test_size=0.25, stratify=labels, random_state=42
    )
    train_ids, test_ids = set(train_ids), set(test_ids)
    print(f"Subject-level split: {len(train_ids)} train subjects, {len(test_ids)} test subjects")
    print("(entire subjects go to one side only — no subject appears in both)\n")

    feature_names = None  # set on first window, verified identical afterward

    def build_dataset(subject_list, id_set):
        nonlocal feature_names
        X, y = [], []
        for s in subject_list:
            if s["subject_id"] not in id_set:
                continue
            windows = windows_for_subject(s["data"], s["fs"])
            for w in windows:
                fv, names = build_feature_vector_and_names(w, s["fs"])
                if feature_names is None:
                    feature_names = names
                else:
                    assert names == feature_names, "Feature name order mismatch between windows!"
                X.append(fv)
                y.append(1 if s["label"] == "ADHD" else 0)
        return np.array(X), np.array(y)

    print("Extracting features for training set (using the SAME function the live server uses)...")
    X_train, y_train = build_dataset(subjects, train_ids)
    print(f"  {len(X_train)} training windows, {X_train.shape[1]} features each")

    print("Extracting features for test set...")
    X_test, y_test = build_dataset(subjects, test_ids)
    print(f"  {len(X_test)} test windows\n")

    # ---- Pipeline: StandardScaler -> calibrated SVC (avoids the ----
    # ---- SVC(probability=True) deprecation, gives real predict_proba) ----
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", CalibratedClassifierCV(
            SVC(kernel="rbf", class_weight="balanced", random_state=42),
            method="sigmoid",
        )),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("=" * 60)
    print(f"Test accuracy (subject-level split, {len(test_ids)} held-out subjects): {accuracy:.4f}")
    print("=" * 60)
    print("\nFull classification report:")
    print(classification_report(y_test, y_pred, target_names=["Control", "ADHD"]))
    print(f"\nNOTE: single train/test split, not k-fold cross-validated. Trained on "
          f"{len(train_ids)} subjects, evaluated on {len(test_ids)} completely unseen subjects.")

    joblib.dump({
        "pipeline": pipeline,
        "feature_names": feature_names,
        "condition": "adhd",
        "cv_accuracy": float(accuracy),
        "cv_std": None,  # honestly None — this is a single split, not cross-validated
        "label_map": {0: "control", 1: "adhd"},
    }, MODEL_OUT_PATH)
    print(f"\nSaved model to {MODEL_OUT_PATH}")


if __name__ == "__main__":
    main()