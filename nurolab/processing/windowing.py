# File: nurolab/processing/windowing.py
# Stage B — Sliding Window Engine
#
# Maintains a rolling buffer and yields fixed-size windows with a fixed stride,
# regardless of whether the underlying EEGDataSource is offline (dataset) or
# live (continuous stream). No branching in downstream code.

import collections
import numpy as np
from nurolab.datasources.base import EEGDataSource


class SlidingWindowEngine:
    """
    Wraps any EEGDataSource and yields analysis windows as numpy arrays.

    Parameters
    ----------
    data_source   : EEGDataSource
    window_sec    : float  — length of each window (default 20 s)
    stride_sec    : float  — step between windows   (default  2 s)
    read_chunk_sec: float  — samples pulled per tick (default  1 s)

    Usage
    -----
    engine = SlidingWindowEngine(src, window_sec=20, stride_sec=2)
    for window in engine.windows():
        # window.shape == (window_n, n_channels)
        features = extract_feature_vector(window, src.sample_rate)
    """

    def __init__(
        self,
        data_source: EEGDataSource,
        window_sec: float = 20.0,
        stride_sec: float = 2.0,
        read_chunk_sec: float = 1.0,
    ):
        self.src = data_source
        self.fs = data_source.sample_rate
        self.win_n = int(window_sec * self.fs)
        self.stride_n = int(stride_sec * self.fs)
        self.read_n = int(read_chunk_sec * self.fs)
        self.buffer = collections.deque(maxlen=self.win_n)
        self._since_last_window = 0
        self._total_samples = 0

    def windows(self):
        """
        Generator. Yields (window_array, metadata) every stride_sec seconds
        once the buffer first fills up.

        Works for BOTH finite datasets (returns when exhausted) and infinite
        live streams (runs until caller breaks or source fails).

        Yields
        ------
        window : np.ndarray of shape (win_n, n_channels)
        meta   : dict with window timing info
        """
        while True:
            chunk = self.src.read_chunk(self.read_n)
            if chunk is None:
                break  # offline source exhausted

            for row in chunk:
                self.buffer.append(row)
                self._since_last_window += 1
                self._total_samples += 1

                if (
                    len(self.buffer) == self.win_n
                    and self._since_last_window >= self.stride_n
                ):
                    self._since_last_window = 0
                    window_end_sample = self._total_samples
                    window_start_sample = window_end_sample - self.win_n
                    meta = {
                        "window_start_time": window_start_sample / self.fs,
                        "window_end_time":   window_end_sample / self.fs,
                        "window_start_sample": window_start_sample,
                        "window_end_sample":   window_end_sample,
                        "n_samples": self.win_n,
                        "n_channels": len(self.src.channel_names),
                    }
                    yield np.array(self.buffer), meta

    def reset(self):
        """Clear the internal buffer (e.g. when switching files)."""
        self.buffer.clear()
        self._since_last_window = 0
        self._total_samples = 0
