# File: nurolab/processing/deviation_engine.py
# Personal Baseline Tracking — Deviation Engine
#
# Tracks how far each live feature vector deviates from a personal
# calibration baseline using Mahalanobis distance and CUSUM.

import numpy as np


class DeviationEngine:
    """
    Tracks deviation of live feature vectors from a personal baseline.

    Built from a set of windows collected during a relaxed calibration phase.
    After calibration:
      - mahalanobis()  → single scalar distance from baseline
      - cusum_update() → per-feature cumulative sum alarms
      - evaluate()     → combined dict for the WebSocket payload

    CUSUM parameters (k, h) follow Page's original formulation:
      k = reference value (half of the shift you want to detect, in σ units)
      h = decision threshold (raise alarm when CUSUM exceeds this)
    """

    def __init__(
        self,
        baseline_X: np.ndarray,
        feature_names: list,
        cusum_k: float = 0.5,
        cusum_h: float = 5.0,
    ):
        """
        Args:
            baseline_X:    (n_windows, n_features) — relaxed baseline windows
            feature_names: list of feature name strings (same order as vectors)
            cusum_k:       CUSUM reference value (default 0.5 σ)
            cusum_h:       CUSUM decision threshold (default 5.0)
        """
        self.feature_names = feature_names
        self.mu = baseline_X.mean(axis=0)
        self.sigma = baseline_X.std(axis=0) + 1e-10

        # Inverse covariance for Mahalanobis distance
        cov = np.cov(baseline_X.T)
        self.cov_inv = np.linalg.pinv(cov)

        # CUSUM state
        self.k = cusum_k
        self.h = cusum_h
        self.cusum_pos = np.zeros(len(self.mu))
        self.cusum_neg = np.zeros(len(self.mu))

    def zscore(self, x: np.ndarray) -> np.ndarray:
        """Per-feature z-score relative to baseline."""
        return (x - self.mu) / self.sigma

    def mahalanobis(self, x: np.ndarray) -> float:
        """
        Mahalanobis distance from baseline mean.
        Accounts for feature correlations; more meaningful than Euclidean.
        """
        d = x - self.mu
        return float(np.sqrt(np.maximum(d @ self.cov_inv @ d, 0.0)))

    def cusum_update(self, z: np.ndarray) -> np.ndarray:
        """
        Update CUSUM with a z-score vector and return alarm mask.
        Resets alarmed features' accumulators (standard CUSUM behavior).

        Returns:
            Boolean array — True where a feature triggered an alarm.
        """
        self.cusum_pos = np.maximum(0.0, self.cusum_pos + z - self.k)
        self.cusum_neg = np.maximum(0.0, self.cusum_neg - z - self.k)
        alarm = (self.cusum_pos > self.h) | (self.cusum_neg > self.h)
        self.cusum_pos[alarm] = 0.0
        self.cusum_neg[alarm] = 0.0
        return alarm

    def evaluate(self, feature_vec: np.ndarray) -> dict:
        """
        Full deviation assessment for one live feature vector.

        Returns dict suitable for the WebSocket payload's 'deviation' block.
        """
        x = np.array(feature_vec, dtype=float)
        z = self.zscore(x)
        alarms = self.cusum_update(z)
        top_idx = int(np.argmax(np.abs(z)))

        return {
            "mahalanobis":      self.mahalanobis(x),
            "z_scores":         z.tolist(),
            "cusum_alarms":     alarms.tolist(),
            "top_deviation_idx":  top_idx,
            "top_deviation_name": self.feature_names[top_idx] if self.feature_names else str(top_idx),
        }

    def reset_cusum(self):
        """Reset CUSUM accumulators (e.g. after a known state change)."""
        self.cusum_pos[:] = 0.0
        self.cusum_neg[:] = 0.0
