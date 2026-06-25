# File: nurolab/tests/test_pipeline.py
# Run: pytest nurolab/tests/test_pipeline.py -v

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from nurolab.datasources.replay_source import SyntheticEEGSource
from nurolab.processing.filters import butter_bandpass, notch_filter, stage_a_pipeline
from nurolab.processing.windowing import SlidingWindowEngine
from nurolab.processing.features import (
    power_spectral_density, differential_entropy, hjorth_parameters,
    hjorth_all_channels, extract_feature_vector, build_feature_names,
)
from nurolab.processing.feature_selection import anova_select, ZScoreNormalizer
from nurolab.processing.deviation_engine import DeviationEngine
from nurolab.ml.explain import explain_prediction, risk_tier_from_mahalanobis


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def synthetic_src():
    return SyntheticEEGSource(n_channels=4, fs=256.0,
                               channel_names=["Fp1", "Fp2", "F3", "F4"])

@pytest.fixture
def sample_window():
    """2 s of 4-channel synthetic data at 256 Hz."""
    rng = np.random.default_rng(0)
    return rng.standard_normal((512, 4)) * 30.0

@pytest.fixture
def filtered_window(sample_window):
    return stage_a_pipeline(sample_window, fs=256.0)


# ── Datasource tests ──────────────────────────────────────────────────────────

class TestSyntheticEEGSource:
    def test_properties(self, synthetic_src):
        assert synthetic_src.sample_rate == 256.0
        assert synthetic_src.n_channels == 4
        assert len(synthetic_src.channel_names) == 4
        assert synthetic_src.is_live() is True

    def test_read_chunk_shape(self, synthetic_src):
        chunk = synthetic_src.read_chunk(256)
        assert chunk is not None
        assert chunk.shape == (256, 4)

    def test_read_chunk_dtype(self, synthetic_src):
        chunk = synthetic_src.read_chunk(128)
        assert np.isfinite(chunk).all(), "Chunk should contain no NaN/Inf"

    def test_multiple_chunks(self, synthetic_src):
        chunks = [synthetic_src.read_chunk(256) for _ in range(5)]
        # Each chunk should be different (not returning the same array)
        assert not np.allclose(chunks[0], chunks[1])


# ── Filter tests ──────────────────────────────────────────────────────────────

class TestFilters:
    def test_bandpass_shape_preserved(self, sample_window):
        out = butter_bandpass(sample_window, fs=256.0)
        assert out.shape == sample_window.shape

    def test_bandpass_finite(self, sample_window):
        out = butter_bandpass(sample_window, fs=256.0)
        assert np.isfinite(out).all()

    def test_notch_shape_preserved(self, sample_window):
        out = notch_filter(sample_window, fs=256.0, freq=50.0)
        assert out.shape == sample_window.shape

    def test_stage_a_reduces_dc(self, sample_window):
        """Bandpass should remove DC offset."""
        dc_signal = sample_window + 1000.0
        filtered = stage_a_pipeline(dc_signal, fs=256.0)
        assert abs(filtered.mean()) < abs(dc_signal.mean())

    def test_nyquist_safety(self, sample_window):
        """Should not raise even if high > Nyquist."""
        out = butter_bandpass(sample_window, fs=256.0, high=200.0)
        assert np.isfinite(out).all()


# ── Windowing tests ───────────────────────────────────────────────────────────

class TestSlidingWindowEngine:
    def test_yields_correct_shape(self, synthetic_src):
        engine = SlidingWindowEngine(synthetic_src, window_sec=2.0, stride_sec=1.0)
        windows = []
        for w, meta in engine.windows():
            windows.append(w)
            if len(windows) == 3:
                break
        assert len(windows) == 3
        expected_n = int(2.0 * 256)
        assert windows[0].shape == (expected_n, 4)

    def test_metadata_keys(self, synthetic_src):
        engine = SlidingWindowEngine(synthetic_src, window_sec=2.0, stride_sec=1.0)
        for w, meta in engine.windows():
            assert "window_start_time" in meta
            assert "window_end_time"   in meta
            break

    def test_stride_timing(self, synthetic_src):
        engine = SlidingWindowEngine(synthetic_src, window_sec=2.0, stride_sec=1.0)
        times = []
        for _, meta in engine.windows():
            times.append(meta["window_start_time"])
            if len(times) == 4:
                break
        diffs = np.diff(times)
        # Each window start should be stride_sec apart
        assert all(abs(d - 1.0) < 0.05 for d in diffs), f"Stride timing off: {diffs}"


# ── Feature extraction tests ──────────────────────────────────────────────────

class TestFeatureExtraction:
    def test_psd_structure(self, filtered_window):
        psd = power_spectral_density(filtered_window, fs=256.0)
        assert len(psd) == 4  # 4 channels
        for ch in psd:
            assert set(psd[ch].keys()) == {"delta", "theta", "alpha", "beta", "gamma"}

    def test_de_finite(self, filtered_window):
        psd = power_spectral_density(filtered_window, fs=256.0)
        de = differential_entropy(psd)
        for ch in de:
            for band, val in de[ch].items():
                assert np.isfinite(val), f"DE not finite: ch={ch} band={band}"

    def test_hjorth_parameters_shape(self):
        x = np.random.randn(512)
        act, mob, comp = hjorth_parameters(x)
        assert isinstance(act, float)
        assert act >= 0, "Activity must be non-negative"

    def test_hjorth_all_channels(self, filtered_window):
        hj = hjorth_all_channels(filtered_window)
        assert len(hj) == 4
        for ch, params in hj.items():
            assert len(params) == 3

    def test_feature_vector_length(self, filtered_window):
        fv = extract_feature_vector(filtered_window, fs=256.0)
        n_ch = 4
        expected = n_ch * (5 + 3)  # 5 DE + 3 Hjorth per channel
        assert len(fv) == expected, f"Expected {expected}, got {len(fv)}"

    def test_feature_vector_finite(self, filtered_window):
        fv = extract_feature_vector(filtered_window, fs=256.0)
        assert np.isfinite(fv).all()

    def test_feature_names_match_vector(self, filtered_window):
        fv = extract_feature_vector(filtered_window, fs=256.0)
        names = build_feature_names(["Fp1", "Fp2", "F3", "F4"])
        assert len(names) == len(fv)


# ── Feature selection tests ───────────────────────────────────────────────────

class TestFeatureSelection:
    def test_anova_mask_shape(self):
        rng = np.random.default_rng(42)
        X = rng.standard_normal((100, 20))
        y = np.array(["a"] * 50 + ["b"] * 50)
        mask = anova_select(X, y)
        assert mask.shape == (20,)
        assert mask.dtype == bool

    def test_zscore_normalizer_round_trip(self):
        rng = np.random.default_rng(0)
        X = rng.standard_normal((50, 10)) * 5 + 3
        norm = ZScoreNormalizer().fit(X)
        X_z = norm.fit_transform(X)
        assert abs(X_z.mean()) < 0.1
        assert abs(X_z.std() - 1.0) < 0.1

    def test_zscore_save_load(self, tmp_path):
        rng = np.random.default_rng(1)
        X = rng.standard_normal((30, 8))
        norm = ZScoreNormalizer().fit(X)
        save_path = str(tmp_path / "norm.npz")
        norm.save(save_path)
        norm2 = ZScoreNormalizer.load(save_path)
        np.testing.assert_allclose(norm.mu, norm2.mu)
        np.testing.assert_allclose(norm.sigma, norm2.sigma)


# ── Deviation engine tests ────────────────────────────────────────────────────

class TestDeviationEngine:
    @pytest.fixture
    def engine_with_baseline(self):
        rng = np.random.default_rng(42)
        baseline = rng.standard_normal((100, 8))
        names = [f"feat_{i}" for i in range(8)]
        return DeviationEngine(baseline, names)

    def test_mahalanobis_baseline_near_zero(self, engine_with_baseline):
        """Baseline mean should have near-zero Mahalanobis distance."""
        dist = engine_with_baseline.mahalanobis(engine_with_baseline.mu)
        assert dist < 1.0

    def test_mahalanobis_outlier_large(self, engine_with_baseline):
        """Large outlier should have large Mahalanobis distance."""
        outlier = engine_with_baseline.mu + 10 * engine_with_baseline.sigma
        dist = engine_with_baseline.mahalanobis(outlier)
        assert dist > 5.0

    def test_evaluate_keys(self, engine_with_baseline):
        rng = np.random.default_rng(99)
        fv = rng.standard_normal(8)
        result = engine_with_baseline.evaluate(fv)
        for key in ("mahalanobis", "z_scores", "cusum_alarms", "top_deviation_idx"):
            assert key in result


# ── XAI explain tests ─────────────────────────────────────────────────────────

class TestExplain:
    def test_explain_returns_strings(self):
        z = [2.5, -1.8, 0.3, -3.2, 0.1]
        names = [f"feature_{i}" for i in range(5)]
        out = explain_prediction(z, names, top_k=3)
        assert len(out) == 3
        assert all(isinstance(s, str) for s in out)

    def test_risk_tier_boundaries(self):
        assert risk_tier_from_mahalanobis(1.0) == 0
        assert risk_tier_from_mahalanobis(3.0) == 1
        assert risk_tier_from_mahalanobis(5.5) == 2
        assert risk_tier_from_mahalanobis(8.0) == 3
