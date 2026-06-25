# File: nurolab/datasources/bonn_epilepsy.py
# Adapter for the Bonn University Epilepsy EEG Dataset (Andrzejak et al. 2001)
# Sets A/B = normal, C/D = interictal, E = ictal seizure
# Single-channel plain-text files, fixed fs = 173.61 Hz

import glob
import numpy as np
from .base import EEGDataSource

BONN_FS = 173.61  # Hz, fixed for this dataset


class BonnEpilepsySource(EEGDataSource):
    """
    Wraps one Bonn dataset .txt file (one of sets A–E).
    Each file = 4097 samples, single channel, ~23.6 seconds.
    """

    SET_LABELS = {
        "A": "normal_eyes_open",
        "B": "normal_eyes_closed",
        "C": "interictal_opposite_hemisphere",
        "D": "interictal_epileptogenic_zone",
        "E": "ictal_seizure",
    }

    BINARY_LABELS = {
        "A": 0,  # normal
        "B": 0,  # normal
        "C": 1,  # interictal
        "D": 1,  # interictal
        "E": 2,  # seizure
    }

    def __init__(self, txt_file_path: str, set_letter: str):
        assert set_letter.upper() in self.SET_LABELS, f"Unknown set: {set_letter}"
        self.set_letter = set_letter.upper()
        self.label = self.SET_LABELS[self.set_letter]
        self.binary_label = self.BINARY_LABELS[self.set_letter]

        self._data = np.loadtxt(txt_file_path).reshape(-1, 1)  # (n, 1)
        self._pos = 0

    @property
    def sample_rate(self) -> float:
        return BONN_FS

    @property
    def channel_names(self) -> list:
        return ["EEG1"]

    @property
    def n_channels(self) -> int:
        return 1

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


def load_bonn_dataset(root_dir: str) -> list:
    """
    root_dir contains subfolders or files named per set (A, B, C, D, E).
    Returns list of (BonnEpilepsySource, binary_label) tuples.
      binary_label: 0=normal (A,B), 1=interictal (C,D), 2=seizure (E)
    """
    sources = []
    for set_letter in ["A", "B", "C", "D", "E"]:
        files = sorted(glob.glob(f"{root_dir}/{set_letter}*/*.txt"))
        if not files:
            files = sorted(glob.glob(f"{root_dir}/*{set_letter}*.txt"))
        for f in files:
            src = BonnEpilepsySource(f, set_letter)
            sources.append((src, src.binary_label))
    return sources
