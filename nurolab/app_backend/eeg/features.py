# File: nurolab/app_backend/eeg/features.py
# Band power + Differential Entropy (DE) feature extraction.
#
# Differential Entropy for a Gaussian-distributed signal segment simplifies to:
#     DE = 0.5 * log(2 * pi * e * variance)
# This is the standard formulation used in EEG emotion/cognitive-state
# literature (e.g. SEED dataset DE features), and is a decent stand-in for
# more expensive spectral-entropy estimates for windowed EEG band power.

from __future__ import annotations

import numpy as np
from scipy import signal

EULER_E = np.e

# Canonical EEG band edges in Hz.
BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def band_power(data: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Average power spectral density within a frequency band using Welch's method.

    Args:
        data: 1D array of samples (single channel, single window)
        fs: sampling rate in Hz
        band: (low_hz, high_hz)

    Returns:
        Mean PSD power in the band (float).
    """
    data = np.asarray(data, dtype=float)
    nperseg = min(len(data), max(int(fs * 2), 8))
    freqs, psd = signal.welch(data, fs=fs, nperseg=nperseg)

    low, high = band
    mask = (freqs >= low) & (freqs <= high)
    if not np.any(mask):
        return 0.0
    return float(np.mean(psd[mask]))


def alpha_power(data: np.ndarray, fs: float) -> float:
    return band_power(data, fs, BANDS["alpha"])


def beta_power(data: np.ndarray, fs: float) -> float:
    return band_power(data, fs, BANDS["beta"])


def theta_power(data: np.ndarray, fs: float) -> float:
    return band_power(data, fs, BANDS["theta"])

def delta_power(data: np.ndarray, fs: float) -> float:
    return band_power(data, fs, BANDS["delta"])


def gamma_power(data: np.ndarray, fs: float) -> float:
    return band_power(data, fs, BANDS["gamma"])


def differential_entropy(power: float) -> float:
    """Differential entropy from band power, assuming Gaussian signal statistics.

    DE = 0.5 * log(2 * pi * e * variance)

    `power` here is used as a proxy for variance (Welch PSD mean over the band),
    which is the standard approximation used for windowed EEG DE features.
    """
    variance = max(power, 1e-12)  # guard against log(0)
    return 0.5 * float(np.log(2 * np.pi * EULER_E * variance))


def compute_band_de(data: np.ndarray, fs: float) -> dict[str, float]:
    """Compute differential entropy for all 5 EEG bands for a single channel window."""
    d_pow = delta_power(data, fs)
    a_pow = alpha_power(data, fs)
    b_pow = beta_power(data, fs)
    t_pow = theta_power(data, fs)
    g_pow = gamma_power(data, fs)
    return {
        "delta_power": d_pow,
        "alpha_power": a_pow,
        "beta_power": b_pow,
        "theta_power": t_pow,
        "gamma_power": g_pow,
        "delta_de": differential_entropy(d_pow),
        "alpha_de": differential_entropy(a_pow),
        "beta_de": differential_entropy(b_pow),
        "theta_de": differential_entropy(t_pow),
        "gamma_de": differential_entropy(g_pow),
    }


def compute_multichannel_de(data: np.ndarray, fs: float) -> dict[str, float]:
    """Average DE features across channels.

    Args:
        data: array of shape (n_channels, n_samples)
        fs: sampling rate

    Returns:
        dict with alpha_de / beta_de / theta_de averaged over channels,
        plus raw band powers.
    """
    data = np.atleast_2d(data)
    per_channel = [compute_band_de(ch, fs) for ch in data]

    keys = per_channel[0].keys()
    return {k: float(np.mean([c[k] for c in per_channel])) for k in keys}


# ── Hjorth parameters + full 5-band DE (used by the clinical SVM models) ────
#
# The uploaded nurolab_epilepsy_svm.pkl / nurolab_depression_svm.pkl models
# were trained on per-channel feature vectors of the form:
#   [delta_DE, theta_DE, alpha_DE, beta_DE, gamma_DE,
#    hjorth_activity, hjorth_mobility, hjorth_complexity]
# This section reproduces that exact feature set.

def hjorth_parameters(data: np.ndarray) -> dict[str, float]:
    """Classic Hjorth Activity / Mobility / Complexity for a single channel.

    Activity   = variance(signal)
    Mobility   = sqrt(variance(diff(signal)) / variance(signal))
    Complexity = Mobility(diff(signal)) / Mobility(signal)
    """
    data = np.asarray(data, dtype=float)
    d1 = np.diff(data)
    d2 = np.diff(d1)

    var0 = np.var(data)
    var1 = np.var(d1)
    var2 = np.var(d2)

    activity = float(var0)
    mobility = float(np.sqrt(var1 / var0)) if var0 > 1e-12 else 0.0
    mobility_d1 = float(np.sqrt(var2 / var1)) if var1 > 1e-12 else 0.0
    complexity = float(mobility_d1 / mobility) if mobility > 1e-12 else 0.0

    return {
        "hjorth_activity": activity,
        "hjorth_mobility": mobility,
        "hjorth_complexity": complexity,
    }


def compute_full_channel_features(data: np.ndarray, fs: float) -> dict[str, float]:
    """Full per-channel feature set matching the clinical SVM models' training features:
    delta/theta/alpha/beta/gamma differential entropy + the 3 Hjorth parameters.

    Returns a dict with keys: delta_DE, theta_DE, alpha_DE, beta_DE, gamma_DE,
    hjorth_activity, hjorth_mobility, hjorth_complexity — these exact suffixes
    are what feature_names in the .pkl metadata use after the channel prefix
    (e.g. "FP1_delta_DE", "FP1_hjorth_activity").
    """
    data = np.asarray(data, dtype=float)

    features = {}
    for band_name in ("delta", "theta", "alpha", "beta", "gamma"):
        power = band_power(data, fs, BANDS[band_name])
        features[f"{band_name}_DE"] = differential_entropy(power)

    features.update(hjorth_parameters(data))
    return features

