# File: nurolab/validation/validate_de_against_seed.py
# Sanity-check our Differential Entropy math against SEED's published values.
#
# Run after downloading a small subset of SEED:
#   python -m nurolab.validation.validate_de_against_seed

import numpy as np
from scipy.io import loadmat
from nurolab.processing.features import power_spectral_density, differential_entropy


def validate_de(
    seed_raw_mat_path: str,
    seed_de_feature_path: str,
    fs: float = 200.0,
):
    """
    Compare our DE against SEED's own pre-computed DE features.

    Args:
        seed_raw_mat_path:    path to a SEED raw .mat EEG recording
        seed_de_feature_path: path to SEED's official extracted DE features
        fs: SEED sample rate (200 Hz)

    SEED .mat key naming follows pattern 'djc_eeg1', 'djc_eeg2', etc.
    Inspect the keys with list(loadmat(path).keys()) if needed.
    """
    raw = loadmat(seed_raw_mat_path)
    official_de = loadmat(seed_de_feature_path)

    # Find the first EEG key
    eeg_keys = [k for k in raw if "eeg" in k.lower() and not k.startswith("_")]
    if not eeg_keys:
        print("ERROR: no 'eeg' key found. Inspect with list(loadmat(path).keys())")
        return
    eeg_key = eeg_keys[0]

    print(f"Using EEG key: '{eeg_key}'")
    signal_matrix = raw[eeg_key]  # shape varies by SEED version

    # Take first 20 s from channel 0
    window_samples = int(fs * 20)
    if signal_matrix.ndim == 2:
        # (n_channels, n_samples) — SEED standard layout
        signal = signal_matrix[0, :window_samples]
    else:
        signal = signal_matrix[:window_samples, 0]

    window = signal.reshape(-1, 1)

    psd = power_spectral_density(window, fs)
    our_de = differential_entropy(psd)

    print("\n── Our DE (5 bands, channel 0, first 20s window) ──")
    for band, val in our_de[0].items():
        print(f"  {band:6s}: {val:+.4f}")

    print("\n── Expected: compare against SEED's official DE for the same window ──")
    print("  Expect the same ORDER OF MAGNITUDE and relative band ranking.")
    print("  Exact values differ slightly due to windowing/nperseg parameters.")

    # Print SEED official DE for reference (structure varies by SEED release)
    de_keys = [k for k in official_de if "de" in k.lower() and not k.startswith("_")]
    if de_keys:
        print(f"\n  SEED DE keys found: {de_keys}")
        k0 = de_keys[0]
        print(f"  official_de['{k0}'] shape: {official_de[k0].shape}")
        print(f"  First trial, first channel, all bands: {official_de[k0][0, 0, :]}")
    else:
        print("  No 'de' keys found in the feature file — inspect manually.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m nurolab.validation.validate_de_against_seed "
              "<raw_mat_path> <de_feature_path>")
        print("Example: python -m nurolab.validation.validate_de_against_seed "
              "data/seed/Preprocessed_EEG/djc_eeg1.mat "
              "data/seed/ExtractedFeatures/djc_de1.mat")
        sys.exit(1)
    validate_de(sys.argv[1], sys.argv[2])
