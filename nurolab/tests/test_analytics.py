# File: nurolab/tests/test_analytics.py
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nurolab.processing.analytics import (
    alpha_beta_ratio,
    engagement_index,
    relaxation_index,
    cognitive_load_index,
    signal_quality_score,
    compute_all_metrics,
)

def test_alpha_beta_ratio():
    result = alpha_beta_ratio(2.0, 1.0)
    assert result > 1.0  # alpha > beta means relaxed
    print(f"✓ alpha_beta_ratio: {result:.4f}")

def test_engagement_index():
    result = engagement_index(1.0, 1.0, 1.0)
    assert result > 0
    print(f"✓ engagement_index: {result:.4f}")

def test_relaxation_index():
    result = relaxation_index(2.0, 1.0)
    assert result > 1.0
    print(f"✓ relaxation_index: {result:.4f}")

def test_cognitive_load():
    result = cognitive_load_index(2.0, 1.0)
    assert result > 1.0
    print(f"✓ cognitive_load_index: {result:.4f}")

def test_signal_quality():
    window = np.random.randn(512, 4) * 30
    score = signal_quality_score(window)
    assert 0.0 <= score <= 1.0
    print(f"✓ signal_quality_score: {score:.2f}")

def test_compute_all_metrics():
    from nurolab.datasources.replay_source import SyntheticEEGSource
    from nurolab.processing.filters import stage_a_pipeline
    from nurolab.processing.features import extract_feature_vector

    src = SyntheticEEGSource(n_channels=4, fs=256.0,
                              channel_names=["Fp1","Fp2","F3","F4"])
    chunk = src.read_chunk(512)
    filtered = stage_a_pipeline(chunk, 256.0)
    fv = extract_feature_vector(filtered, 256.0)
    metrics = compute_all_metrics(fv, ["Fp1","Fp2","F3","F4"])

    assert "alpha_de" in metrics
    assert "engagement_index" in metrics
    assert "relaxation_index" in metrics
    assert "cognitive_load" in metrics
    assert len(metrics) == 9
    print(f"✓ compute_all_metrics: {len(metrics)} metrics computed")
    for k, v in metrics.items():
        print(f"   {k}: {v:.4f}")

if __name__ == "__main__":
    test_alpha_beta_ratio()
    test_engagement_index()
    test_relaxation_index()
    test_cognitive_load()
    test_signal_quality()
    test_compute_all_metrics()
    print("\nAll analytics tests passed ✓")