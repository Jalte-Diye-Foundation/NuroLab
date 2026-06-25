# File: nurolab/processing/features.py
# Stage C–E — Feature Extraction
#
# Produces named, interpretable feature vectors for each window.
# Features are organized per channel for per-channel XAI downstream.
#
# Per channel (5 bands × 2 spectral features) + 3 Hjorth = 13 features/channel
# Optional: PLI connectivity matrix (n_ch*(n_ch-1)/2 pairs)

import numpy as np
from scipy import signal as sig
from scipy.signal import hilbert

# ── Frequency bands ───────────────────────────────────────────────────────────

BANDS = {
    "delta": (1.0,  3.0),
    "theta": (4.0,  7.0),
    "alpha": (8.0, 13.0),
    "beta":  (14.0, 30.0),
    "gamma": (31.0, 50.0),
}
BAND_NAMES = list(BANDS.keys())
HJORTH_NAMES = ["activity", "mobility", "complexity"]


# ── Spectral features ─────────────────────────────────────────────────────────

def power_spectral_density(window: np.ndarray, fs: float, nperseg: int = 512) -> dict:
    """
    Welch PSD for each channel across all frequency bands.

    Args:
        window:  (n_samples, n_channels)
        fs:      sampling rate Hz
        nperseg: Welch segment length (clamped to window length)

    Returns:
        {ch_idx: {band_name: mean_band_power}}
    """
    n_ch = window.shape[1]
    result = {}
    for ch in range(n_ch):
        nperseg_actual = min(nperseg, window.shape[0])
        freqs, psd = sig.welch(
            window[:, ch], fs=fs, nperseg=nperseg_actual, window="hann"
        )
        result[ch] = {}
        for band, (lo, hi) in BANDS.items():
            mask = (freqs >= lo) & (freqs <= hi)
            result[ch][band] = float(np.mean(psd[mask])) if mask.any() else 0.0
    return result


def differential_entropy(psd_dict: dict) -> dict:
    """
    DE = ln(PSD). Numerically stable (floor at 1e-12 before log).

    Args:
        psd_dict: {ch: {band: psd_value}}

    Returns:
        {ch: {band: de_value}}
    """
    de = {}
    for ch, bands in psd_dict.items():
        de[ch] = {b: float(np.log(max(v, 1e-12))) for b, v in bands.items()}
    return de


# ── Hjorth parameters ─────────────────────────────────────────────────────────

def hjorth_parameters(x: np.ndarray) -> tuple:
    """
    Compute Hjorth activity, mobility, complexity for a 1D signal.

    Returns:
        (activity, mobility, complexity) as floats
    """
    activity = float(np.var(x))
    dx = np.diff(x)
    mobility = float(np.sqrt(np.var(dx) / (activity + 1e-12)))
    ddx = np.diff(dx)
    mobility_dx = float(np.sqrt(np.var(ddx) / (np.var(dx) + 1e-12)))
    complexity = float(mobility_dx / (mobility + 1e-12))
    return activity, mobility, complexity


def hjorth_all_channels(window: np.ndarray) -> dict:
    """
    Hjorth parameters for all channels.

    Returns:
        {ch_idx: (activity, mobility, complexity)}
    """
    return {ch: hjorth_parameters(window[:, ch]) for ch in range(window.shape[1])}


# ── Phase Lag Index connectivity ──────────────────────────────────────────────

def pli_matrix(window: np.ndarray, fs: float, band: str = "alpha") -> np.ndarray:
    """
    Phase Lag Index between all channel pairs for a given band.
    PLI is robust to volume conduction (unlike coherence).

    Args:
        window:  (n_samples, n_channels)
        fs:      sampling rate Hz
        band:    one of BANDS keys

    Returns:
        (n_channels, n_channels) symmetric PLI matrix
    """
    lo, hi = BANDS[band]
    n_ch = window.shape[1]
    sos = sig.butter(4, [lo, hi], btype="band", fs=fs, output="sos")

    phase = np.zeros_like(window)
    for ch in range(n_ch):
        filt = sig.sosfilt(sos, window[:, ch])
        phase[:, ch] = np.angle(hilbert(filt))

    pli = np.zeros((n_ch, n_ch))
    for i in range(n_ch):
        for j in range(i + 1, n_ch):
            dphi = phase[:, i] - phase[:, j]
            pli[i, j] = pli[j, i] = float(
                abs(np.mean(np.sign(np.sin(dphi))))
            )
    return pli


# ── Feature naming ────────────────────────────────────────────────────────────

def build_feature_names(channel_names: list, include_connectivity: bool = False) -> list:
    """
    Returns the ordered list of feature names matching extract_feature_vector().

    Args:
        channel_names:        list of channel label strings
        include_connectivity: whether PLI features are included

    Returns:
        List of feature name strings (same order as the feature vector)
    """
    names = []
    for ch_name in channel_names:
        for b in BAND_NAMES:
            names.append(f"{ch_name}_{b}_DE")
        for h in HJORTH_NAMES:
            names.append(f"{ch_name}_hjorth_{h}")

    if include_connectivity:
        n_ch = len(channel_names)
        for i in range(n_ch):
            for j in range(i + 1, n_ch):
                names.append(f"PLI_{channel_names[i]}_{channel_names[j]}_alpha")

    return names


# ── Main extraction entry point ───────────────────────────────────────────────

def extract_feature_vector(
    window: np.ndarray,
    fs: float,
    include_connectivity: bool = False,
    conn_band: str = "alpha",
) -> np.ndarray:
    """
    Full Stage C–E feature extraction for one window.

    Args:
        window:               (n_samples, n_channels), filtered (Stage A applied)
        fs:                   sampling rate Hz
        include_connectivity: if True, append PLI connectivity features
        conn_band:            frequency band for PLI ('alpha' default)

    Returns:
        Flat numpy float64 array of length:
          n_channels * (5 DE + 3 Hjorth)
          [+ n_channels*(n_channels-1)//2 PLI values if include_connectivity]
    """
    n_ch = window.shape[1]
    psd = power_spectral_density(window, fs)
    de = differential_entropy(psd)
    hj = hjorth_all_channels(window)

    feat = []
    for ch in range(n_ch):
        for b in BAND_NAMES:
            feat.append(de[ch][b])
        feat.extend(list(hj[ch]))

    if include_connectivity:
        pli = pli_matrix(window, fs, band=conn_band)
        for i in range(n_ch):
            for j in range(i + 1, n_ch):
                feat.append(float(pli[i, j]))

    return np.array(feat, dtype=np.float64)
