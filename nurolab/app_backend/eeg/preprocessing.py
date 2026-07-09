# File: nurolab/app_backend/eeg/preprocessing.py
# Signal preprocessing: bandpass filter, notch filter, normalization.
#
# These operate on numpy arrays shaped (n_channels, n_samples) or (n_samples,).
# scipy.signal is used for actual filter design so the math is correct
# rather than hand-rolled approximations.

from __future__ import annotations

import numpy as np
from scipy import signal


def bandpass_filter(
    data: np.ndarray,
    fs: float,
    low_hz: float = 1.0,
    high_hz: float = 45.0,
    order: int = 4,
) -> np.ndarray:
    """Zero-phase Butterworth bandpass filter.

    Args:
        data: array of shape (n_channels, n_samples) or (n_samples,)
        fs: sampling rate in Hz
        low_hz / high_hz: passband edges
        order: filter order

    Returns:
        Filtered array, same shape as input.
    """
    nyq = fs / 2.0
    low = max(low_hz / nyq, 1e-6)
    high = min(high_hz / nyq, 0.999999)
    if low >= high:
        raise ValueError(f"Invalid bandpass range: low={low_hz}Hz high={high_hz}Hz fs={fs}Hz")

    sos = signal.butter(order, [low, high], btype="bandpass", output="sos")
    axis = -1
    return signal.sosfiltfilt(sos, data, axis=axis)


def notch_filter(
    data: np.ndarray,
    fs: float,
    freq_hz: float = 60.0,
    quality_factor: float = 30.0,
) -> np.ndarray:
    """IIR notch filter to remove mains-hum interference (50/60 Hz).

    Args:
        data: array of shape (n_channels, n_samples) or (n_samples,)
        fs: sampling rate in Hz
        freq_hz: frequency to notch out (60 for US mains, 50 for EU/most of world)
        quality_factor: higher = narrower notch
    """
    nyq = fs / 2.0
    if freq_hz >= nyq:
        # Nothing to notch if the target frequency is above Nyquist.
        return data
    b, a = signal.iirnotch(freq_hz / nyq, quality_factor)
    return signal.filtfilt(b, a, data, axis=-1)


def normalize(data: np.ndarray, method: str = "zscore") -> np.ndarray:
    """Normalize signal per-channel.

    Args:
        data: array of shape (n_channels, n_samples) or (n_samples,)
        method: "zscore" or "minmax"
    """
    data = np.asarray(data, dtype=float)
    axis = -1

    if method == "zscore":
        mean = np.mean(data, axis=axis, keepdims=True)
        std = np.std(data, axis=axis, keepdims=True)
        std = np.where(std < 1e-12, 1.0, std)
        return (data - mean) / std

    if method == "minmax":
        dmin = np.min(data, axis=axis, keepdims=True)
        dmax = np.max(data, axis=axis, keepdims=True)
        rng = np.where((dmax - dmin) < 1e-12, 1.0, dmax - dmin)
        return (data - dmin) / rng

    raise ValueError(f"Unknown normalization method: {method}")


def preprocess_pipeline(
    data: np.ndarray,
    fs: float,
    mains_hz: float = 50.0,
    band: tuple[float, float] = (1.0, 45.0),
) -> np.ndarray:
    """Full Stage-A preprocessing chain: notch -> bandpass -> normalize."""
    x = notch_filter(data, fs, freq_hz=mains_hz)
    x = bandpass_filter(x, fs, low_hz=band[0], high_hz=band[1])
    x = normalize(x, method="zscore")
    return x
