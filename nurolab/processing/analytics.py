# Analytics Engine — Stage C metrics
# Computes meaningful brain state metrics from raw DE feature values.
# These are the numbers that get displayed in the app.

import numpy as np


def alpha_beta_ratio(alpha_de: float, beta_de: float) -> float:
    """
    Alpha/Beta ratio — higher means more relaxed.
    Typical values: > 1.0 relaxed, < 0.5 stressed.
    """
    return alpha_de / (beta_de + 1e-10)


def engagement_index(beta_de: float, alpha_de: float, theta_de: float) -> float:
    """
    Engagement index — higher means more mentally engaged.
    Formula from Pope et al. 1995, widely used in BCI literature.
    """
    return beta_de / (alpha_de + theta_de + 1e-10)


def relaxation_index(alpha_de: float, beta_de: float) -> float:
    """
    Relaxation index — inverse of engagement.
    Higher means more relaxed and less mentally active.
    """
    return alpha_de / (beta_de + 1e-10)


def cognitive_load_index(theta_de: float, alpha_de: float) -> float:
    """
    Cognitive load index — higher theta/alpha means higher mental workload.
    Validated against NASA-TLX in multiple studies.
    """
    return theta_de / (alpha_de + 1e-10)


def signal_quality_score(window: np.ndarray) -> float:
    """
    Estimates EEG signal quality from 0.0 to 1.0.
    Low quality if signal is flat (electrode off) or extremely noisy.

    Args:
        window: (n_samples, n_channels) filtered EEG window

    Returns:
        Float between 0.0 and 1.0. Above 0.7 is acceptable quality.
    """
    variance = float(np.var(window))
    if variance < 1.0:
        return 0.1   # flat signal — electrode likely off
    if variance > 10000:
        return 0.3   # extreme noise — movement artifact
    return min(1.0, variance / 1000.0)


def compute_all_metrics(feature_vector: np.ndarray, channel_names: list) -> dict:
    """
    Computes all analytics metrics from a feature vector.
    Expects features named like 'Fp1_alpha_DE', 'Fp1_beta_DE' etc.
    Returns a dict ready to include in the WebSocket JSON payload.

    Args:
        feature_vector: 1D numpy array from extract_feature_vector()
        channel_names:  list of channel name strings

    Returns:
        dict with all computed metrics
    """
    from nurolab.processing.features import build_feature_names

    names = build_feature_names(channel_names)
    feat = dict(zip(names, feature_vector))

    # Average DE values across all channels for each band
    def avg_band(band):
        vals = [v for k, v in feat.items() if f"_{band}_DE" in k]
        return float(np.mean(vals)) if vals else 0.0

    alpha = avg_band("alpha")
    beta  = avg_band("beta")
    theta = avg_band("theta")
    delta = avg_band("delta")
    gamma = avg_band("gamma")

    return {
        "alpha_de":           alpha,
        "beta_de":            beta,
        "theta_de":           theta,
        "delta_de":           delta,
        "gamma_de":           gamma,
        "alpha_beta_ratio":   alpha_beta_ratio(alpha, beta),
        "engagement_index":   engagement_index(beta, alpha, theta),
        "relaxation_index":   relaxation_index(alpha, beta),
        "cognitive_load":     cognitive_load_index(theta, alpha),
    }