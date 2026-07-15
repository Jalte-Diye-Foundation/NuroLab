# File: nurolab/app_backend/eeg/streaming.py
# Simulated EEG stream generator + async producer.
#
# This is a placeholder data source. To integrate real hardware later,
# implement a class with the same `.read_window()` interface (see
# `HardwareEEGSource` stub at the bottom) and swap it in `server.py`.

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import numpy as np


class SimulatedEEGSource:
    """Generates synthetic multi-channel EEG-like signal windows.

    Not clinically meaningful data — pure sine + noise, useful for
    exercising the full pipeline (preprocessing -> features -> predictions)
    without real hardware attached.

    Defaults (fs=250.0, 8 channels named Fp1/Fp2/F3/F4/T7/T8/O1/O2) are
    chosen to exactly match the physical NuroLab headset design: the
    ADS1299 AFE's native data-rate options don't include 256 SPS (it
    supports 250/500/1k/2k/4k/8k/16k SPS), so 250 is the real achievable
    rate — and the channel names/order match the 8 physical electrode
    positions wired in the hardware interconnection document, so a
    HardwareEEGSource swap-in requires no downstream code changes.
    """

    def __init__(
        self,
        n_channels: int = 8,
        fs: float = 250.0,
        window_sec: float = 2.0,
        channel_names: list[str] | None = None,
        seed: int | None = None,
    ):
        self.n_channels = n_channels
        self.fs = fs
        self.window_sec = window_sec
        self.n_samples = int(fs * window_sec)
        self.channel_names = channel_names or (
            ["Fp1", "Fp2", "F3", "F4", "T7", "T8", "O1", "O2"][:n_channels]
            if n_channels <= 8 else [f"ch{i}" for i in range(n_channels)]
        )
        self._rng = np.random.default_rng(seed)
        self._t0 = 0.0

    def read_window(self) -> np.ndarray:
        """Return one window of shape (n_channels, n_samples)."""
        t = self._t0 + np.arange(self.n_samples) / self.fs
        self._t0 += self.window_sec

        window = np.zeros((self.n_channels, self.n_samples))
        for ch in range(self.n_channels):
            alpha_wave = 1.0 * np.sin(2 * np.pi * 10 * t + ch)     # ~10 Hz alpha
            beta_wave = 0.5 * np.sin(2 * np.pi * 20 * t + ch * 2)  # ~20 Hz beta
            theta_wave = 0.7 * np.sin(2 * np.pi * 6 * t + ch * 3)  # ~6 Hz theta
            noise = self._rng.normal(0, 0.3, size=self.n_samples)
            window[ch] = alpha_wave + beta_wave + theta_wave + noise

        return window


async def eeg_producer(
    source: SimulatedEEGSource,
    interval_sec: float = 2.0,
) -> AsyncGenerator[np.ndarray, None]:
    """Async generator yielding EEG windows at a fixed cadence.

    Usage:
        async for window in eeg_producer(source):
            ...
    """
    while True:
        yield source.read_window()
        await asyncio.sleep(interval_sec)


class HardwareEEGSource:
    """DEPRECATED — superseded by HeadsetIngestBuffer (see eeg/headset_ingest.py).

    Real hardware now pushes data INTO the backend over a WebSocket
    (ws://<host>/ws/ingest/headset), rather than the backend pulling from a
    local read_window() call — this matches how the ESP32-S3 firmware
    actually delivers samples (WiFi push), not a local serial/BLE poll.
    See HARDWARE_BACKEND_INTERCONNECTION.md for the full protocol and
    rationale. This class is kept only so old imports don't hard-crash;
    it intentionally still raises if instantiated.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "HardwareEEGSource is deprecated. Use HeadsetIngestBuffer + the "
            "/ws/ingest/headset endpoint in server.py instead — see "
            "HARDWARE_BACKEND_INTERCONNECTION.md."
        )
