# File: nurolab/datasources/replay_source.py
# Simulates real-time streaming from ANY offline dataset OR generates
# synthetic EEG-shaped noise. Lets the whole team work in parallel
# before hardware exists.

import time
import numpy as np
from .base import EEGDataSource


class ReplaySource(EEGDataSource):
    """
    Wraps any offline EEGDataSource and replays it with real
    timing delays, simulating a live device. Loops when exhausted.

    Use this to stress-test the full pipeline (filters + windowing +
    feature extraction + server) without waiting for hardware.
    """

    def __init__(self, offline_source: EEGDataSource, loop: bool = True):
        self._src = offline_source
        self._loop = loop
        print(f"[ReplaySource] Loading {offline_source.__class__.__name__} into memory...")
        self._buffer = self._load_all()
        print(f"[ReplaySource] Loaded {len(self._buffer)} samples ({len(self._buffer)/self.sample_rate:.1f}s)")
        self._pos = 0
        self._last_read_time = None

    def _load_all(self) -> np.ndarray:
        chunks = []
        chunk_size = int(self._src.sample_rate)  # 1 second at a time
        while True:
            c = self._src.read_chunk(chunk_size)
            if c is None:
                break
            chunks.append(c)
        if not chunks:
            raise ValueError("Offline source yielded no data.")
        return np.vstack(chunks)

    @property
    def sample_rate(self) -> float:
        return self._src.sample_rate

    @property
    def channel_names(self) -> list:
        return self._src.channel_names

    @property
    def n_channels(self) -> int:
        return self._src.n_channels

    def is_live(self) -> bool:
        return True  # behaves like a live stream for the pipeline

    def read_chunk(self, n_samples: int):
        # Real-time pacing: block until enough wall-clock time has passed
        if self._last_read_time is not None:
            elapsed = time.time() - self._last_read_time
            needed = n_samples / self.sample_rate
            if elapsed < needed:
                time.sleep(needed - elapsed)
        self._last_read_time = time.time()

        end = self._pos + n_samples
        if end > len(self._buffer):
            if not self._loop:
                return None
            self._pos = 0
            end = n_samples

        chunk = self._buffer[self._pos:end]
        self._pos = end
        return chunk

    def close(self):
        self._src.close()


class SyntheticEEGSource(EEGDataSource):
    """
    Generates fake but EEG-shaped multi-channel signal:
      - Pink (1/f) noise baseline
      - 10 Hz alpha rhythm
      - Occasional blink artefacts on Fp1/Fp2

    Useful for:
      - App UI development with zero real data
      - Testing the WebSocket server immediately
      - Filter / windowing / feature pipeline smoke tests
    """

    def __init__(
        self,
        n_channels: int = 8,
        fs: float = 256.0,
        channel_names: list = None,
    ):
        self._n_ch = n_channels
        self._fs = fs
        self._names = channel_names or [f"CH{i+1}" for i in range(n_channels)]
        self._t = 0.0
        self._last_read_time = None
        self._rng = np.random.default_rng(seed=42)

    @property
    def sample_rate(self) -> float:
        return self._fs

    @property
    def channel_names(self) -> list:
        return self._names

    @property
    def n_channels(self) -> int:
        return self._n_ch

    def is_live(self) -> bool:
        return True

    def read_chunk(self, n_samples: int):
        # Real-time pacing
        if self._last_read_time is not None:
            elapsed = time.time() - self._last_read_time
            needed = n_samples / self._fs
            if elapsed < needed:
                time.sleep(needed - elapsed)
        self._last_read_time = time.time()

        t_axis = self._t + np.arange(n_samples) / self._fs
        self._t = t_axis[-1] + 1.0 / self._fs

        sig = np.zeros((n_samples, self._n_ch))
        for ch in range(self._n_ch):
            # Pink noise: integrate white noise
            pink = np.cumsum(self._rng.standard_normal(n_samples)) * 0.5
            # Alpha rhythm: 10 Hz with per-channel phase offset
            alpha = 15.0 * np.sin(2 * np.pi * 10.0 * t_axis + ch * 0.4)
            # White noise floor
            noise = self._rng.standard_normal(n_samples) * 3.0
            sig[:, ch] = pink + alpha + noise

            # Random blink artefact ~1% of chunks, on frontal channels only
            if ch < 2 and self._rng.random() < 0.01:
                blink_start = self._rng.integers(0, max(1, n_samples - 50))
                blink_len = min(50, n_samples - blink_start)
                sig[blink_start:blink_start + blink_len, ch] += 150.0

        return sig

    def close(self):
        pass
