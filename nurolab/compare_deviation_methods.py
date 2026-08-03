# File: compare_deviation_methods_v3.py
#
# Stage 4, corrected: same real recording, zero new downloads. Fixes two
# bugs from v2 — (1) DE-feature filtering was applied AFTER calibration/
# session splits, so baseline_X stayed 320-wide while feature_names got
# shortened, causing an IndexError; (2) alpha_idx was computed on the
# OLD 320-wide list while beta_idx/theta_idx were computed on the NEW
# ~200-wide list, silently pointing at the wrong features. Here, ALL
# filtering happens immediately after loading, before anything else
# touches the data — so every downstream index is consistent.
#
# Run with: python compare_deviation_methods_v3.py

import numpy as np

from nurolab.datasources.openneuro_depression import OpenNeuroDepressionSource
from nurolab.data.processing.blink_remover import OnlineBlinkRemover
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.features import extract_feature_vector, build_feature_names
from nurolab.processing.deviation_engine import DeviationEngine
from nurolab.app_backend.services import analytics_service
from nurolab.app_backend.models.database import Baseline

FILE_PATH = "nurolab/data/sub-hc1_ses-hc_task-rest_eeg.bdf"
CHUNK_SIZE = 512
WINDOW_SEC = 20.0
STRIDE_SEC = 2.0
NOTCH_FREQ = 50.0

# Calibration = LAST N windows (later, stable stretch).
# Test = everything BEFORE that (includes the real anomaly from v1).
N_CALIBRATION_WINDOWS = 40


def collect_feature_vectors(file_path: str):
    src = OpenNeuroDepressionSource(file_path)
    fs = src.sample_rate
    n_ch = src.n_channels

    blink_remover = OnlineBlinkRemover(
        fs=fs, n_channels=n_ch, fp1_idx=src.fp1_idx or 0, fp2_idx=src.fp2_idx or 1
    )
    feature_names = build_feature_names(src.channel_names)

    cleaned_buffer = np.zeros((0, n_ch))
    win_samples = int(WINDOW_SEC * fs)
    step_samples = int(STRIDE_SEC * fs)
    feature_vectors = []

    while True:
        raw_chunk = src.read_chunk(CHUNK_SIZE)
        if raw_chunk is None:
            break
        cleaned_chunk, _, _, _ = blink_remover.process(raw_chunk)
        cleaned_buffer = np.vstack([cleaned_buffer, cleaned_chunk])

        while len(cleaned_buffer) >= win_samples:
            epoch = cleaned_buffer[:win_samples, :]
            filtered = stage_a_pipeline(epoch, fs, notch_freq=NOTCH_FREQ)
            fv = extract_feature_vector(filtered, fs)
            feature_vectors.append(fv)
            cleaned_buffer = cleaned_buffer[step_samples:, :]

    return feature_vectors, feature_names, fs


def zscore_method(alpha_de, beta_de, theta_de, baseline: Baseline):
    current = {"alpha": alpha_de, "beta": beta_de, "theta": theta_de}
    deviation_score = analytics_service.compute_deviation(current, baseline)
    risk_tier = analytics_service.compute_risk(deviation_score)
    return deviation_score, risk_tier


def main():
    print(f"Loading real recording: {FILE_PATH}")
    raw_feature_vectors, raw_feature_names, fs = collect_feature_vectors(FILE_PATH)
    n_total = len(raw_feature_vectors)
    print(f"Extracted {n_total} windows, {len(raw_feature_names)} raw features each")

    # ---- Filter to DE-only features FIRST, before anything else touches the data ----
    de_indices = [i for i, name in enumerate(raw_feature_names) if name.endswith("_DE")]
    feature_vectors = [fv[de_indices] for fv in raw_feature_vectors]
    feature_names = [raw_feature_names[i] for i in de_indices]
    n_features = len(feature_names)
    print(f"Filtered to DE-only features: {n_features} features each (dropped Hjorth params)\n")

    if n_total <= N_CALIBRATION_WINDOWS:
        raise RuntimeError(f"Only {n_total} windows available, need more than {N_CALIBRATION_WINDOWS}.")

    # ---- NOW split, using the already-filtered, consistent feature_vectors ----
    calibration_fvs = feature_vectors[-N_CALIBRATION_WINDOWS:]
    session_fvs = feature_vectors[:-N_CALIBRATION_WINDOWS]
    print(f"Calibration: {len(calibration_fvs)} windows (LAST {N_CALIBRATION_WINDOWS} — a later, stable stretch)")
    print(f"Session (test): {len(session_fvs)} windows (FIRST {len(session_fvs)} — includes the known EXG7 anomaly from v1)\n")

    # ---- Honest math check on the FILTERED covariance ----
    baseline_X = np.array(calibration_fvs)
    cov = np.cov(baseline_X.T)
    rank = np.linalg.matrix_rank(cov)
    print(f"Covariance matrix rank: {rank} out of {n_features} features")
    print(f"  → {rank}/{n_features} = {100*rank/n_features:.1f}% of feature space is informed by real calibration data.\n")

    # ---- All 3 indices computed on the SAME filtered feature_names list ----
    alpha_idx = feature_names.index("Fp1_alpha_DE")
    beta_idx = feature_names.index("Fp1_beta_DE")
    theta_idx = feature_names.index("Fp1_theta_DE")

    cal_alpha = [fv[alpha_idx] for fv in calibration_fvs]
    cal_beta = [fv[beta_idx] for fv in calibration_fvs]
    cal_theta = [fv[theta_idx] for fv in calibration_fvs]

    baseline = Baseline(
        alpha_mean=float(np.mean(cal_alpha)), beta_mean=float(np.mean(cal_beta)), theta_mean=float(np.mean(cal_theta)),
        alpha_std=float(np.std(cal_alpha)) or 1e-6, beta_std=float(np.std(cal_beta)) or 1e-6, theta_std=float(np.std(cal_theta)) or 1e-6,
        n_samples=len(cal_alpha), quality="good",
    )

    engine = DeviationEngine(baseline_X, feature_names)

    print(f"{'Window':<8} {'Z-score dev':<14} {'Z-score tier':<14} {'Mahalanobis':<14} {'Top feature (Mahalanobis)':<25}")
    print("-" * 80)
    for i, fv in enumerate(session_fvs):
        z_dev, z_tier = zscore_method(fv[alpha_idx], fv[beta_idx], fv[theta_idx], baseline)
        m_result = engine.evaluate(fv)
        print(f"{i+1:<8} {z_dev:<14.2f} {z_tier:<14} {m_result['mahalanobis']:<14.2f} {m_result['top_deviation_name']:<25}")

    print("\nCheck: does the rank % look better than the 12.2% from the 320-feature run?")
    print("Do the Mahalanobis values look stable now, or still swinging wildly window to window?")


if __name__ == "__main__":
    main()