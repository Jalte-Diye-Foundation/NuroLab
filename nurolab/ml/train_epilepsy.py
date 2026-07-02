import sys, numpy as np, joblib
from pathlib import Path
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_selection import SelectFpr, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nurolab.datasources.bonn_epilepsy_csv import load_bonn_csv_dataset
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.features import extract_feature_vector, build_feature_names

CSV_PATH  = PROJECT_ROOT / "nurolab" / "data" / "bonn_eeg" / "Epileptic Seizure Recognition.csv"
MODEL_OUT = PROJECT_ROOT / "models" / "nurolab_epilepsy_svm.pkl"


def build_dataset():
    segments, labels, fs = load_bonn_csv_dataset(str(CSV_PATH))
    feat_names = build_feature_names(["EEG1"])

    X, y = [], []
    for seg, label in zip(segments, labels):
        epoch = seg.reshape(-1, 1)
        filtered = stage_a_pipeline(epoch, fs)
        fv = extract_feature_vector(filtered, fs)
        X.append(fv)
        y.append(label)

    return np.array(X, dtype=float), np.array(y), feat_names


if __name__ == "__main__":
    print("=" * 60)
    print("NuroLab — Epilepsy Model Training (Kaggle CSV)")
    print("=" * 60)

    MODEL_OUT.parent.mkdir(exist_ok=True)
    print(f"\nLoading from {CSV_PATH}...")
    X, y, feat_names = build_dataset()

    unique, counts = np.unique(y, return_counts=True)
    label_map = {0: "normal", 1: "interictal", 2: "seizure"}
    print(f"Dataset : {X.shape[0]} segments | {X.shape[1]} features")
    print(f"Classes : { {label_map[k]: int(v) for k, v in zip(unique, counts)} }")

    pipeline = Pipeline([
        ("select", SelectFpr(f_classif, alpha=0.05)),
        ("scale",  StandardScaler()),
        ("clf",    CalibratedClassifierCV(
                       SVC(kernel="linear", C=1.0, decision_function_shape="ovo"),
                       ensemble=False)),
    ])

    n_splits = 5
    print(f"\nCross-validating ({n_splits}-fold stratified)...")
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy")
    print(f"CV accuracy : {scores.mean():.3f} ± {scores.std():.3f}")
    print(f"Per-fold    : {[round(s, 3) for s in scores]}")
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