# File: nurolab/datasources/bonn_epilepsy_csv.py
import numpy as np
import pandas as pd
from pathlib import Path

LABEL_MAP_5_TO_3 = {
    1: 2,  # seizure       -> seizure
    2: 1,  # tumor area    -> interictal
    3: 1,  # healthy area  -> interictal
    4: 0,  # eyes closed   -> normal
    5: 0,  # eyes open     -> normal
}


def load_bonn_csv_dataset(csv_path: str):
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(p)
    if df.columns[0].lower() in ("unnamed: 0", "id", ""):
        df = df.iloc[:, 1:]

    x_cols = [c for c in df.columns if c.upper().startswith("X")]
    if not x_cols or "y" not in df.columns:
        raise ValueError(f"Unexpected CSV format. Found columns: {list(df.columns)[:5]}...")

    segments = df[x_cols].to_numpy(dtype=float)
    raw_labels = df["y"].to_numpy(dtype=int)
    labels = np.array([LABEL_MAP_5_TO_3[v] for v in raw_labels])

    fs = 178.0
    return segments, labels, fs