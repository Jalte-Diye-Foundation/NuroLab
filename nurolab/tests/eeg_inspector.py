# File: nurolab/processing/eeg_inspector.py
#
# EEG File Inspector
# -------------------
# A quick "health check" for an EEG recording file.
#
# Before a researcher uses a dataset, they usually want to know, at a glance:
#   - Is the file valid / does it open at all?
#   - How long is the recording?
#   - How many channels does it have, and what are they called?
#   - What is the sampling rate?
#   - Roughly what do the EEG band powers (delta/theta/alpha/beta/gamma) look like?
#
# This script answers all of that from the command line, e.g.:
#   python nurolab/processing/eeg_inspector.py path/to/recording.bdf
#
# Supported formats: .bdf (BioSemi) and .set (EEGLAB). Both are read using
# MNE-Python (https://mne.tools), the standard open-source library for EEG/MEG
# data in Python, so we don't have to write our own file-format parsers.

import sys
from pathlib import Path

import numpy as np

# Let this script be run either as `python nurolab/processing/eeg_inspector.py ...`
# or imported as `from nurolab.processing.eeg_inspector import inspect_eeg_file`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# EEG frequency bands, in Hz (fairly standard definitions used in EEG research).
BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 45),
}


def _load_raw(file_path: str):
    """
    Loads an EEG file into an MNE Raw object based on its extension.
    Raises a clear error for unsupported formats instead of failing deep
    inside a library call.
    """
    import mne

    mne.set_log_level("ERROR")  # keep MNE's internal logging out of our output

    suffix = Path(file_path).suffix.lower()

    if suffix == ".bdf":
        raw = mne.io.read_raw_bdf(file_path, preload=True)
    elif suffix == ".set":
        raw = mne.io.read_raw_eeglab(file_path, preload=True)
    else:
        raise ValueError(
            f"Unsupported file format '{suffix}'. This inspector currently "
            f"supports .bdf and .set files."
        )

    return raw


def _band_power_summary(raw) -> dict:
    """
    Computes average band power (in dB, relative log power) per EEG band,
    averaged across all channels, using Welch's method for the power
    spectral density (PSD). This is a standard way to summarize how much
    signal energy falls into each classic EEG frequency band.

    Returns a dict like {"delta": ..., "theta": ..., ...} of floats.
    """
    from scipy.signal import welch

    data = raw.get_data()          # shape: (n_channels, n_samples)
    sfreq = raw.info["sfreq"]

    # nperseg controls frequency resolution; cap it at the data length so this
    # doesn't break on very short recordings.
    nperseg = int(min(sfreq * 2, data.shape[1]))
    if nperseg < 8:
        raise ValueError("Recording is too short to compute band power.")

    freqs, psd = welch(data, fs=sfreq, nperseg=nperseg, axis=-1)
    # psd shape: (n_channels, n_freqs) -> average across channels
    mean_psd = psd.mean(axis=0)

    band_power = {}
    for band_name, (low, high) in BANDS.items():
        mask = (freqs >= low) & (freqs <= high)
        if not np.any(mask):
            band_power[band_name] = float("nan")
            continue
        # Average power in-band, converted to dB for a more readable scale.
        power = mean_psd[mask].mean()
        band_power[band_name] = float(10 * np.log10(power)) if power > 0 else float("-inf")

    return band_power


def inspect_eeg_file(file_path: str) -> dict:
    """
    Reads an EEG file and prints + returns a summary of its contents.

    Supports .bdf and .set formats.

    Args:
        file_path: path to the EEG file

    Returns:
        dict with recording information (also printed to the console):
            file, sampling_rate, n_channels, channel_names,
            duration_sec, duration_min, total_samples, band_power_db
    """
    path = Path(file_path)
    print(f"\nInspecting: {file_path}")
    print("=" * 60)

    if not path.exists():
        print(f"✗ File not found: {file_path}")
        raise FileNotFoundError(file_path)

    try:
        raw = _load_raw(file_path)
    except ValueError as e:
        print(f"✗ {e}")
        raise
    except Exception as e:
        print(f"✗ Could not read file (it may be corrupted or malformed): {e}")
        raise

    sfreq = raw.info["sfreq"]
    n_channels = len(raw.ch_names)
    n_samples = raw.n_times
    duration_sec = n_samples / sfreq
    duration_min = duration_sec / 60

    print(f"Sampling rate  : {sfreq:.0f} Hz")
    print(f"Channels       : {n_channels}")
    shown = raw.ch_names[:8]
    print(f"Channel names  : {shown}{'...' if n_channels > 8 else ''}")
    print(f"Duration       : {duration_sec:.1f}s ({duration_min:.1f} minutes)")
    print(f"Total samples  : {n_samples}")

    band_power = {}
    try:
        band_power = _band_power_summary(raw)
        print("\nBand power summary (dB, averaged across all channels):")
        print(f"  Delta : {band_power['delta']:.3f}")
        print(f"  Theta : {band_power['theta']:.3f}")
        print(f"  Alpha : {band_power['alpha']:.3f}")
        print(f"  Beta  : {band_power['beta']:.3f}")
        print(f"  Gamma : {band_power['gamma']:.3f}")
    except Exception as e:
        print(f"\n(Skipped band power summary: {e})")

    summary = {
        "file": file_path,
        "sampling_rate": float(sfreq),
        "n_channels": n_channels,
        "channel_names": raw.ch_names,
        "duration_sec": round(duration_sec, 2),
        "duration_min": round(duration_min, 2),
        "total_samples": int(n_samples),
        "band_power_db": band_power,
    }

    print("\n✓ File inspection complete")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nurolab/processing/eeg_inspector.py <path_to_eeg_file>")
        print("Example: python nurolab/processing/eeg_inspector.py nurolab/data/sub-hc1_ses-hc_task-rest_eeg.bdf")
        sys.exit(1)

    try:
        inspect_eeg_file(sys.argv[1])
    except Exception:
        sys.exit(1)
