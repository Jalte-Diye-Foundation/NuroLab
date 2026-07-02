# File: nurolab/processing/filters.py
# Stage A — Temporal Filtering
#
# Three operations applied to raw EEG (µV, shape (n_samples, n_channels)):
#   1. Butterworth bandpass (0.1–70 Hz, order 5 -> effective 10th-order zero-phase)
#   2. IIR Notch (50 Hz, Q=30) for AC line interference
#   3. Optional per-channel z-score normalization
#
# Uses sosfiltfilt (forward + reverse pass) for zero phase distortion.

import numpy as np
from scipy import signal as sig


def butter_bandpass(
    data: np.ndarray,
    fs: float,
    low: float = 0.1,
    high: float = 70.0,
    order: int = 5,
) -> np.ndarray:
    """
    Zero-phase Butterworth bandpass filter.
    order=5 + sosfiltfilt (forward+reverse) = effective 10th-order roll-off.

    Args:
        data:  (n_samples, n_channels) in µV
        fs:    sampling rate in Hz
        low:   lower cutoff Hz (default 0.1)
        high:  upper cutoff Hz (default 70.0)
        order: filter order (default 5)

    Returns:
        Filtered array, same shape as input.
    """
    nyq = fs / 2.0
    high = min(high, nyq - 1.0)  # safety clamp below Nyquist
    sos = sig.butter(order, [low, high], btype="band", fs=fs, output="sos")
    out = np.zeros_like(data, dtype=float)
    for ch in range(data.shape[1]):
        out[:, ch] = sig.sosfiltfilt(sos, data[:, ch])
    return out


def notch_filter(
    data: np.ndarray,
    fs: float,
    freq: float = 50.0,
    q: float = 30.0,
) -> np.ndarray:
    """
    Zero-phase IIR notch filter — removes AC line interference.

    Args:
        data:  (n_samples, n_channels) in µV
        fs:    sampling rate in Hz
        freq:  notch frequency Hz (50 for India/EU, 60 for US)
        q:     quality factor (higher = narrower notch)

    Returns:
        Filtered array, same shape as input.
    """
    b, a = sig.iirnotch(freq, Q=q, fs=fs)
    out = np.zeros_like(data, dtype=float)
    for ch in range(data.shape[1]):
        out[:, ch] = sig.filtfilt(b, a, data[:, ch])
    return out


def normalize_signal(data: np.ndarray) -> np.ndarray:
    """
    Per-channel z-score normalization of raw EEG signal — zero mean,
    unit variance for each channel. Applied at the signal level (Stage A),
    not to be confused with feature-level normalization in Stage F
    (processing/feature_selection.py).

    Args:
        data: (n_samples, n_channels) in µV

    Returns:
        Normalized array, same shape as input.
    """
    mean = np.mean(data, axis=0, keepdims=True)
    std = np.std(data, axis=0, keepdims=True) + 1e-10
    return (data - mean) / std


def stage_a_pipeline(
    raw_data: np.ndarray,
    fs: float,
    notch_freq: float = 50.0,
    normalize: bool = False,
) -> np.ndarray:
    """
    Full Stage A: bandpass then notch, with optional normalization.

    Args:
        raw_data:   (n_samples, n_channels) in µV
        fs:         sampling rate in Hz
        notch_freq: 50.0 (India/EU) or 60.0 (US)
        normalize:  if True, z-score normalize the signal after filtering

    Returns:
        Filtered (and optionally normalized) array, same shape as input.
    """
    filtered = butter_bandpass(raw_data, fs)
    filtered = notch_filter(filtered, fs, freq=notch_freq)
    if normalize:
        filtered = normalize_signal(filtered)
    return filtered