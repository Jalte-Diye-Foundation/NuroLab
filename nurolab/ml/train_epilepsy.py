# File: nurolab/ml/train_epilepsy.py
#
# Trains a linear SVM on the Bonn University Epilepsy Dataset.
# Each Bonn .txt file is already an independent 23.6s recording from a
# different patient/electrode site, so standard StratifiedKFold is fine
# here — there is no shared-subject leakage risk the way there was with
# multi-window-per-subject EEG datasets like ds003478.
#
# SETUP:
#   1. Download: https://www.kaggle.com/datasets/harunshimanto/epileptic-seizure-recognition
#   2. Unzip into: <project_root>/data/bonn_eeg/A/, B/, C/, D/, E/
#   3. Run: python -m nurolab.ml.train_epilepsy

import sys, numpy as np, joblib
from pathlib import Path
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_selection import SelectFpr, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

from nurolab.datasources.bonn_epilepsy import load_bonn_dataset
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.features import extract_feature_vector, build_feature_names

BONN_ROOT   = PROJECT_ROOT / "data" / "bonn_eeg"
MODEL_OUT   = PROJECT_ROOT / "models" / "nurolab_epilepsy_svm.pkl"
SEGMENT_SEC = 23


def build_dataset():
    sources = load_bonn_dataset(str(BONN_ROOT))
    if not sources:
        raise FileNotFoundError(
            f"\nNo Bonn .txt files found under {BONN_ROOT}\n"
            "Download: https://www.kaggle.com/datasets/harunshimanto/epileptic-seizure-recognition\n"
            "Unzip into data/bonn_eeg/A/, B/, C/, D/, E/"
        )
    feat_names = build_feature_names(["EEG1"])
    X, y = [], []
    for src, label in sources:
        chunk = src.read_chunk(int(src.sample_rate * SEGMENT_SEC))
        if chunk is None or len(chunk) < src.sample_rate * 4:
            continue
        filtered = stage_a_pipeline(chunk, src.sample_rate)
        fv = extract_feature_vector(filtered, src.sample_rate)
        X.append(fv)
        y.append(label)
    return np.array(X, dtype=float), np.array(y), feat_names


if __name__ == "__main__":
    print("=" * 60)
    print("NuroLab — Epilepsy Model Training (Bonn Dataset)")
    print("=" * 60)

    MODEL_OUT.parent.mkdir(exist_ok=True)
    print(f"\nLoading from {BONN_ROOT}...")
    X, y, feat_names = build_dataset()

    unique, counts = np.unique(y, return_counts=True)
    label_map = {0: "normal", 1: "interictal", 2: "seizure"}
    print(f"Dataset : {X.shape[0]} segments | {X.shape[1]} features")
    print(f"Classes : { {label_map[k]:int(v) for k,v in zip(unique,counts)} }")

    # Feature selection lives INSIDE the pipeline — no leakage into CV folds
    pipeline = Pipeline([
        ("select", SelectFpr(f_classif, alpha=0.05)),
        ("scale",  StandardScaler()),
        ("clf",    CalibratedClassifierCV(
                       SVC(kernel="linear", C=1.0, decision_function_shape="ovo"),
                       ensemble=False)),
    ])

    n_splits = min(5, int(min(counts)))
    print(f"\nCross-validating ({n_splits}-fold stratified)...")
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy")
    print(f"CV accuracy : {scores.mean():.3f} ± {scores.std():.3f}")
    print(f"Per-fold    : {[round(s,3) for s in scores]}")
    print("Literature  : 99.5% with multiscale Hjorth (Rizal et al. 2023)")

    pipeline.fit(X, y)
    joblib.dump({
        "pipeline":      pipeline,
        "feature_names": feat_names,
        "condition":     "epilepsy",
        "cv_accuracy":   float(scores.mean()),
        "cv_std":        float(scores.std()),
        "cv_per_fold":   scores.tolist(),
        "label_map":     {0: "normal", 1: "interictal", 2: "seizure"},
    }, MODEL_OUT)
    print(f"\nSaved → {MODEL_OUT}")
