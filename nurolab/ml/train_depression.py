# File: nurolab/ml/train_depression.py
#
# Trains a linear SVM on ds003478 (OpenNeuro Depression Rest)
#
# Uses SUBJECT-WISE cross-validation (GroupKFold) to prevent leakage —
# windows from the same subject NEVER appear in both train and test folds.
# Feature selection happens INSIDE the CV pipeline, not before it.
#
# SETUP:
#   1. Download from https://openneuro.org/datasets/ds003478/versions/1.1.0
#   2. Place under <project_root>/data/ds003478/
#   3. Run: python -m nurolab.ml.train_depression

import glob, sys, numpy as np, joblib
from pathlib import Path
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectFpr, f_classif
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold, cross_val_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from nurolab.datasources.openneuro_depression import (
    OpenNeuroDepressionSource, load_depression_labels,
)
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.windowing import SlidingWindowEngine
from nurolab.processing.features import extract_feature_vector, build_feature_names

BIDS_ROOT  = PROJECT_ROOT / "data" / "ds003478"
MODEL_OUT  = PROJECT_ROOT / "models" / "nurolab_depression_svm.pkl"
WINDOW_SEC = 10.0
STRIDE_SEC = 5.0


def build_dataset():
    """
    Returns X, y, groups, feat_names.
    groups[i] = subject ID for window i — REQUIRED for subject-wise CV.
    """
    labels_map = load_depression_labels(str(BIDS_ROOT))

    set_files = sorted(glob.glob(str(BIDS_ROOT / "sub-*" / "eeg" / "*_eeg.set")))
    bdf_files = sorted(glob.glob(str(BIDS_ROOT / "sub-*" / "eeg" / "*_eeg.bdf")))
    all_files = set_files + bdf_files

    if not all_files:
        raise FileNotFoundError(
            f"\nNo EEG files found under {BIDS_ROOT}/sub-*/eeg/\n"
            "Download from: https://openneuro.org/datasets/ds003478/versions/1.1.0\n"
        )

    X, y, groups = [], [], []
    feat_names = None
    expected_len = None
    skipped_label = 0
    skipped_shape = 0
    skipped_files = 0

    print(f"  Found {len(all_files)} EEG files")
    subjects_with_valid_labels = [f for f in all_files if labels_map.get(Path(f).parts[-3]) is not None]
    print(f"  Subjects with valid labels: {len(subjects_with_valid_labels)}")

    for f in all_files:
        sub_id = Path(f).parts[-3]
        label  = labels_map.get(sub_id)
        if label is None:
            skipped_label += 1
            continue

        print(f"  {sub_id} ({label}) — {Path(f).name}")
        try:
            src = OpenNeuroDepressionSource(f, subject_label=label)
        except Exception as e:
            print(f"    WARNING: could not load — {e}")
            skipped_files += 1
            continue

        if feat_names is None:
            feat_names   = build_feature_names(src.channel_names)
            expected_len = len(feat_names)

        engine = SlidingWindowEngine(src, window_sec=WINDOW_SEC, stride_sec=STRIDE_SEC)
        window_count = 0
        for window, _ in engine.windows():
            window_count += 1
            filtered = stage_a_pipeline(window, src.sample_rate)
            fv = extract_feature_vector(filtered, src.sample_rate)
            if len(fv) != expected_len:
                if len(fv) > expected_len:
                    fv = fv[:expected_len]
                else:
                    fv = np.pad(fv, (0, expected_len - len(fv)))
                skipped_shape += 1
            X.append(fv)
            y.append(label)
            groups.append(sub_id)   # <-- track which subject this window came from
        print(f"    {window_count} windows extracted")

    print(f"  (skipped {skipped_label} subclinical subjects — BDI 7-12)")
    if skipped_files:
        print(f"  (failed to load {skipped_files} files)")
    if skipped_shape:
        print(f"  (padded/trimmed {skipped_shape} windows with mismatched channels)")
    return (np.array(X, dtype=float), np.array(y), np.array(groups), feat_names)


if __name__ == "__main__":
    print("=" * 60)
    print("NuroLab — Depression Model Training (ds003478)")
    print("Subject-wise CV (GroupKFold) — no leakage")
    print("=" * 60)

    MODEL_OUT.parent.mkdir(exist_ok=True)
    print(f"\nScanning {BIDS_ROOT} for EEG files...")
    X, y, groups, feat_names = build_dataset()

    if len(X) == 0:
        print("ERROR: No windows extracted. Check your data folder.")
        raise SystemExit(1)

    unique_y, counts_y = np.unique(y, return_counts=True)
    unique_subs = np.unique(groups)
    print(f"\nDataset  : {X.shape[0]} windows | {X.shape[1]} features")
    print(f"Subjects : {len(unique_subs)} total")
    print(f"Classes  : { {k:int(v) for k,v in zip(unique_y,counts_y)} }")

    if len(unique_y) < 2:
        print("\nERROR: Need both 'depressed' and 'control' subjects.")
        raise SystemExit(1)

    n_groups = len(unique_subs)
    if n_groups < 3:
        print(f"\nWARNING: Only {n_groups} subjects total. Subject-wise CV needs "
              f"at least as many subjects as folds. Results will be unstable until "
              f"you add more subjects (aim for 10+ per class).")
    n_splits = min(5, n_groups)

    # ── Pipeline: feature selection + scaling INSIDE cross-validation ────────
    # SelectFpr replaces manual ANOVA — it's the sklearn-native equivalent and
    # composes correctly inside a Pipeline so CV folds never leak into selection.
    pipeline = Pipeline([
        ("select", SelectFpr(f_classif, alpha=0.05)),
        ("scale",  StandardScaler()),
        ("clf",    CalibratedClassifierCV(SVC(kernel="linear", C=1.0), ensemble=False)),
    ])

    print(f"\nCross-validating ({n_splits}-fold GroupKFold, subject-wise)...")
    cv = GroupKFold(n_splits=n_splits)
    scores = cross_val_score(pipeline, X, y, groups=groups, cv=cv, scoring="accuracy")
    print(f"CV accuracy : {scores.mean():.3f} ± {scores.std():.3f}")
    print(f"Per-fold    : {[round(s,3) for s in scores]}")
    print("Literature  : 75-85% with similar spectral features (Cavanagh et al.)")
    print("\nNote: with very few subjects, GroupKFold accuracy can still look")
    print("unstable or high/low by chance. Treat this as directional until you")
    print("have 10+ subjects per class — not yet a number to report as final.")

    # Fit final pipeline on ALL data for deployment (this is fine — it's not
    # used to report accuracy, the CV score above is the honest number)
    pipeline.fit(X, y)
    joblib.dump({
        "pipeline":      pipeline,
        "feature_names": feat_names,
        "condition":     "depression",
        "cv_accuracy":   float(scores.mean()),
        "cv_std":        float(scores.std()),
        "cv_per_fold":   scores.tolist(),
        "n_subjects":    int(n_groups),
    }, MODEL_OUT)
    print(f"\nSaved → {MODEL_OUT}")
