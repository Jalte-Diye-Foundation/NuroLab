# File: nurolab/datasources/adhd_loader.py
#
# Loader for the "EEG Dataset for ADHD" (Kaggle, danizo mirror of the
# open-access IEEE 19-channel ADHD dataset, 61 ADHD + 60 control
# children). Confirmed specs: 128 Hz, 19 channels (10-20 system),
# recorded during a visual attention task.
#
# The raw file is a single flat table: one row per time-sample, with
# 19 channel voltage columns + Class (ADHD/Control) + ID (subject
# identifier, e.g. "v10p"). This loader groups rows back into
# per-subject continuous recordings.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FS = 128.0  # confirmed sampling rate for this dataset

CHANNEL_COLUMNS = [
    "Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2",
    "F7", "F8", "T7", "T8", "P7", "P8", "Fz", "Cz", "Pz",
]


def load_subjects(file_path: str) -> list[dict]:
    """Loads the raw flat file and groups it into one entry per subject.

    Returns a list of dicts, each with:
        "subject_id": str  (e.g. "v10p")
        "label": str       ("ADHD" or "Control")
        "data": np.ndarray shape (n_samples, 19) — continuous recording
        "fs": float        (128.0)
    """
    path = Path(file_path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        print("Warning: loading from Excel is much slower than CSV for "
              "a file this size — consider using the original .csv if you have it.")
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    missing_cols = set(CHANNEL_COLUMNS + ["Class", "ID"]) - set(df.columns)
    if missing_cols:
        raise ValueError(f"File is missing expected columns: {missing_cols}")

    subjects = []
    for subject_id, group in df.groupby("ID"):
        labels = group["Class"].unique()
        if len(labels) != 1:
            print(f"Warning: subject {subject_id} has multiple labels {labels}, using the first one.")
        label = labels[0]

        data = group[CHANNEL_COLUMNS].to_numpy(dtype=float)
        subjects.append({
            "subject_id": subject_id,
            "label": label,
            "data": data,
            "fs": FS,
        })

    return subjects


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python nurolab/datasources/adhd_loader.py <path_to_file>")
        sys.exit(1)

    subjects = load_subjects(sys.argv[1])
    n_adhd = sum(1 for s in subjects if s["label"] == "ADHD")
    n_control = sum(1 for s in subjects if s["label"] == "Control")

    print(f"Loaded {len(subjects)} subjects total")
    print(f"  ADHD: {n_adhd}")
    print(f"  Control: {n_control}")
    print(f"\nFirst subject: {subjects[0]['subject_id']}, label={subjects[0]['label']}, "
          f"data shape={subjects[0]['data'].shape} "
          f"({subjects[0]['data'].shape[0] / FS:.1f} seconds of recording)")