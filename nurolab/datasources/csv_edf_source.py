import numpy as np
import pandas as pd
from pathlib import Path
from .base import EEGDataSource


class CSVEEGSource(EEGDataSource):
    """Reads a plain CSV file containing EEG samples — one row per sample, one column per channel."""

    def __init__(self, csv_path: str, sample_rate: float = None, channel_names: list = None):
        p = Path(csv_path)
        if not p.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        df = pd.read_csv(p)
        ts_col = next((c for c in df.columns if c.lower() in ("timestamp", "time", "t")), None)
        if ts_col is not None:
            timestamps = df[ts_col].values
            data_cols = [c for c in df.columns if c != ts_col]
            if sample_rate is None and len(timestamps) > 1:
                dt = np.median(np.diff(timestamps))
                sample_rate = 1.0 / dt if dt > 0 else 256.0
        else:
            data_cols = list(df.columns)
            if sample_rate is None:
                raise ValueError("No timestamp column found and sample_rate not provided.")

        self._data = df[data_cols].to_numpy(dtype=float)
        self._fs = float(sample_rate)
        self._channels = channel_names or data_cols
        self._pos = 0
        lookup = {ch.upper().replace(" ", ""): idx for idx, ch in enumerate(self._channels)}
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


class EDFEEGSource(EEGDataSource):
    """Reads standard EDF files — the vendor-neutral cousin of BDF."""

    def __init__(self, edf_path: str, subject_label: str = None):
        import mne
        p = Path(edf_path)
        if p.suffix.lower() != ".edf":
            raise ValueError(f"Expected .edf file, got: {p.suffix}")

        raw = mne.io.read_raw_edf(str(p), preload=True, verbose=False)
        raw.pick("eeg")
        self._data = raw.get_data().T * 1e6
        self._fs = float(raw.info["sfreq"])
        self._channels = raw.ch_names
        self._pos = 0
        self.label = subject_label
        lookup = {ch.upper().replace(" ", ""): idx for idx, ch in enumerate(self._channels)}
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