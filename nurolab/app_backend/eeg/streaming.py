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
    """

    def __init__(
        self,
        n_channels: int = 8,
        fs: float = 256.0,
        window_sec: float = 2.0,
        channel_names: list[str] | None = None,
        seed: int | None = None,
    ):
        self.n_channels = n_channels
        self.fs = fs
        self.window_sec = window_sec
        self.n_samples = int(fs * window_sec)
        self.channel_names = channel_names or [f"ch{i}" for i in range(n_channels)]
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
    """Stub for a real EEG device integration.

    To integrate real hardware:
      1. Implement __init__ to open the device connection (serial port,
         BLE, LSL stream, etc).
      2. Implement read_window() to return a (n_channels, n_samples) array
         pulled from the live device buffer.
      3. Swap SimulatedEEGSource for HardwareEEGSource in server.py —
         no other code changes required, since eeg_producer() and all
         downstream processing only depend on the read_window() interface.
    """

    def __init__(self, port: str, fs: float = 256.0, n_channels: int = 8):
        self.port = port
        self.fs = fs
        self.n_channels = n_channels
        raise NotImplementedError(
            "HardwareEEGSource is a placeholder. Implement device I/O here "
            "when real EEG hardware is available."
        )

    def read_window(self) -> np.ndarray:
        raise NotImplementedError
