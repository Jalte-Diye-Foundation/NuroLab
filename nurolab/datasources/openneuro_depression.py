# File: nurolab/datasources/openneuro_depression.py
# Adapter for ds003478 — OpenNeuro Depression Rest dataset
# Files are in EEGLAB .set format (not .bdf)
# BDI >= 13 -> 'depressed'  (as per Cavanagh lab protocol for this dataset)
# BDI <  7  -> 'control'

import numpy as np
import pandas as pd
import mne
from pathlib import Path
from .base import EEGDataSource


class OpenNeuroDepressionSource(EEGDataSource):
    """
    Wraps a single subject's resting-state EEG recording from ds003478.
    Supports both .set (EEGLAB) and .bdf formats — auto-detected by extension.
    Yields chunks in microvolts.
    """

    def __init__(self, eeg_file_path: str, subject_label: str = None):
        p = Path(eeg_file_path)
        ext = p.suffix.lower()

        if ext == ".set":
            raw = mne.io.read_raw_eeglab(str(p), preload=True, verbose=False)
        elif ext == ".bdf":
            raw = mne.io.read_raw_bdf(str(p), preload=True, verbose=False)
        else:
            raise ValueError(f"Unsupported EEG format: {ext}. Expected .set or .bdf")

        raw.pick("eeg")

        self._data = raw.get_data().T          # (n_samples, n_channels)
        self._data = self._data * 1e6          # volts -> µV
        self._fs = float(raw.info["sfreq"])
        self._channels = raw.ch_names
        self._pos = 0
        self.label = subject_label             # 'depressed' or 'control'

        # Channel lookup for blink remover compatibility
        lookup = {ch.upper().replace(" ", ""): idx
                  for idx, ch in enumerate(self._channels)}
        self.fp1_idx = lookup.get("FP1")
        self.fp2_idx = lookup.get("FP2")

    @property
    def sample_rate(self) -> float:
        return self._fs

    @property
    def channel_names(self) -> list:
        return self._channels

    @property
    def n_channels(self) -> int:
        return len(self._channels)

    def is_live(self) -> bool:
        return False

    def read_chunk(self, n_samples: int):
        if self._pos >= len(self._data):
            return None
        end = min(self._pos + n_samples, len(self._data))
        chunk = self._data[self._pos:end]
        self._pos = end
        return chunk

    def reset(self):
        self._pos = 0


def load_depression_labels(bids_root: str) -> dict:
    """
    Load BDI-based labels from participants.tsv.
    ds003478 threshold: BDI >= 13 -> depressed, BDI < 7 -> control
    (Subjects between 7-12 are excluded as subclinical in many analyses)

    Returns dict {participant_id: 'depressed' | 'control' | None}
    """
    tsv_path = Path(bids_root) / "participants.tsv"
    if not tsv_path.exists():
        raise FileNotFoundError(f"participants.tsv not found at {tsv_path}")
    
    df = pd.read_csv(tsv_path, sep="\t")
    labels = {}
    for _, row in df.iterrows():
        bdi = row.get("BDI", None)
        if pd.isna(bdi):
            labels[row["participant_id"]] = None
            continue
        if bdi >= 13:
            labels[row["participant_id"]] = "depressed"
        elif bdi < 7:
            labels[row["participant_id"]] = "control"
        else:
            labels[row["participant_id"]] = None  # subclinical — skip in training
    return labels


def load_subject_metadata(eeg_path: str) -> dict:
    """
    Load companion _events.tsv and _channels.tsv if they exist.
    Works for both .set and .bdf BIDS sidecars.
    """
    p = Path(eeg_path)
    stem = p.stem.replace("_eeg", "")
    return {
        "events":   pd.read_csv(p.parent / f"{stem}_events.tsv", sep="\t")
                    if (p.parent / f"{stem}_events.tsv").exists() else None,
        "channels": pd.read_csv(p.parent / f"{stem}_channels.tsv", sep="\t")
                    if (p.parent / f"{stem}_channels.tsv").exists() else None,
    }
