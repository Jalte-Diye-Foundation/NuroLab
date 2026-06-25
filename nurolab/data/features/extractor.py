import numpy as np
from scipy.signal import welch

# Frequency bands configuration as per dataset standards
FREQUENCY_BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 14.0),
    "beta":  (14.0, 30.0),
    "gamma": (30.0, 47.0)
}

class OnlineFeatureExtractor:
    def __init__(self, fs):
        self.fs = fs

    def _compute_hjorth(self, epoch_data):
        """Compute Hjorth parameters for each EEG channel."""
        diff1 = np.diff(epoch_data, axis=0)
        diff2 = np.diff(diff1, axis=0)

        activity = np.var(epoch_data, axis=0)
        mobility = np.sqrt(np.clip(np.var(diff1, axis=0) / np.clip(activity, 1e-12, None), 1e-12, None))
        complexity = np.sqrt(
            np.clip(np.var(diff2, axis=0) / np.clip(np.var(diff1, axis=0), 1e-12, None), 1e-12, None)
            / np.clip(mobility, 1e-12, None)
        )

        return activity, mobility, complexity

    def compute_de_and_psd(self, epoch_data):
        """
        Computes Differential Entropy (DE), Log Power Spectral Density (PSD),
        and Hjorth parameters for all channels across canonical frequency bands.
        
        Parameters:
            epoch_data (numpy.ndarray): Matrix shape (samples, channels) e.g., (2048, 40)
            
        Returns:
            dict: Flattened dictionary containing calculated DE, PSD and Hjorth features.
        """
        n_samples, n_channels = epoch_data.shape
        
        freqs, psd = welch(epoch_data, fs=self.fs, axis=0, nperseg=min(self.fs, n_samples))
        
        features = {}
        
        for band_name, (low_f, high_f) in FREQUENCY_BANDS.items():
            band_idx = np.where((freqs >= low_f) & (freqs <= high_f))[0]
            
            if len(band_idx) == 0:
                closest_idx = np.argmin(np.abs(freqs - ((low_f + high_f) / 2)))
                band_idx = np.array([closest_idx])

            band_power = psd[band_idx, :]
            mean_power = np.trapz(band_power, freqs[band_idx], axis=0)
            mean_power = np.clip(mean_power / max(1, len(band_idx)), 1e-12, None)
            
            log_psd = np.log10(mean_power)
            de = 0.5 * np.log(2 * np.pi * np.e * mean_power)
            
            for ch_idx in range(n_channels):
                features[f"ch{ch_idx}_{band_name}_de"] = de[ch_idx]
                features[f"ch{ch_idx}_{band_name}_psd"] = log_psd[ch_idx]

        activity, mobility, complexity = self._compute_hjorth(epoch_data)
        for ch_idx in range(n_channels):
            features[f"ch{ch_idx}_hjorth_activity"] = activity[ch_idx]
            features[f"ch{ch_idx}_hjorth_mobility"] = mobility[ch_idx]
            features[f"ch{ch_idx}_hjorth_complexity"] = complexity[ch_idx]

        return features