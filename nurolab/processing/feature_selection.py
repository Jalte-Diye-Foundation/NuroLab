# File: nurolab/processing/feature_selection.py
# Stage F — Feature Selection and Normalization
#
# ANOVA keeps only statistically significant features.
# ZScoreNormalizer is fit once on training data, then applied to live vectors.

import numpy as np
from scipy.stats import f_oneway


def anova_select(
    feature_matrix: np.ndarray,
    labels: np.ndarray,
    p_thresh: float = 0.05,
) -> np.ndarray:
    """
    One-way ANOVA feature selection: keep features that differ
    significantly across class labels.

    Args:
        feature_matrix: (n_windows, n_features)
        labels:         (n_windows,) — any hashable class labels
        p_thresh:       significance threshold (default 0.05)

    Returns:
        Boolean mask array of length n_features.
        True = feature passes significance test.
    """
    classes = np.unique(labels)
    if len(classes) < 2:
        raise ValueError("Need >= 2 classes for ANOVA feature selection.")

    keep = np.zeros(feature_matrix.shape[1], dtype=bool)
    for feat_idx in range(feature_matrix.shape[1]):
        groups = [feature_matrix[labels == c, feat_idx] for c in classes]
        if any(len(g) < 2 for g in groups):
            continue  # not enough samples for this class
        _, p = f_oneway(*groups)
        keep[feat_idx] = p < p_thresh

    return keep


class ZScoreNormalizer:
    """
    Fit once on a baseline / training set; apply consistently to all
    subsequent feature vectors, including live ones.

    Preserves µ and σ so they can be saved and reloaded.
    """

    def __init__(self):
        self.mu: np.ndarray = None
        self.sigma: np.ndarray = None

    def fit(self, feature_matrix: np.ndarray) -> "ZScoreNormalizer":
        """
        Args:
            feature_matrix: (n_windows, n_features) training features

        Returns:
            self (for chaining)
        """
        self.mu = feature_matrix.mean(axis=0)
        self.sigma = feature_matrix.std(axis=0) + 1e-10
        return self

    def transform(self, feature_vec: np.ndarray) -> np.ndarray:
        """
        Args:
            feature_vec: 1D array of length n_features

        Returns:
            Z-scored feature vector
        """
        if self.mu is None:
            raise RuntimeError("ZScoreNormalizer not fitted — call fit() first.")
        return (feature_vec - self.mu) / self.sigma

    def fit_transform(self, feature_matrix: np.ndarray) -> np.ndarray:
        self.fit(feature_matrix)
        return np.vstack([self.transform(row) for row in feature_matrix])

    def save(self, path: str):
        """Save µ and σ to a .npz file."""
        np.savez(path, mu=self.mu, sigma=self.sigma)

    @classmethod
    def load(cls, path: str) -> "ZScoreNormalizer":
        """Load from a .npz file."""
        data = np.load(path)
        obj = cls()
        obj.mu = data["mu"]
        obj.sigma = data["sigma"]
        return obj
