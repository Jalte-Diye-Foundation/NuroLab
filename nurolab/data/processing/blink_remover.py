import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi, iirnotch, tf2sos, find_peaks

# CONFIGURATION
BANDPASS_LOW = 0.5
BANDPASS_HIGH = 15.0
NOTCH_FREQ = 50.0
NOTCH_Q = 30
BUFFER_SECONDS = 4.0
MIN_BLINK_DISTANCE_MS = 400
BLINK_WINDOW_MS = 200
MIN_THRESHOLD = 80e-6
MAD_MULTIPLIER = 6.0

class OnlineBlinkRemover:
    def __init__(self, fs, n_channels, fp1_idx, fp2_idx):
        self.fs = fs
        self.n_channels = n_channels
        self.fp1_idx = fp1_idx
        self.fp2_idx = fp2_idx

        self.bandpass_sos = butter(4, [BANDPASS_LOW, BANDPASS_HIGH], btype="bandpass", fs=fs, output="sos")
        b_notch, a_notch = iirnotch(w0=NOTCH_FREQ, Q=NOTCH_Q, fs=fs)
        self.notch_sos = tf2sos(b_notch, a_notch)

        self.bp_zi = np.repeat(sosfilt_zi(self.bandpass_sos)[:, :, np.newaxis], n_channels, axis=2)
        self.notch_zi = np.repeat(sosfilt_zi(self.notch_sos)[:, :, np.newaxis], n_channels, axis=2)

        self.buffer_size = int(BUFFER_SECONDS * fs)
        self.frontal_buffer = np.zeros(self.buffer_size)

        self.global_sample = 0
        self.last_blink_sample = -100000

        self.min_distance = int(MIN_BLINK_DISTANCE_MS * fs / 1000)
        self.blink_window = int(BLINK_WINDOW_MS * fs / 1000)

    def process(self, chunk):
        filtered, self.bp_zi = sosfilt(self.bandpass_sos, chunk, axis=0, zi=self.bp_zi)
        filtered, self.notch_zi = sosfilt(self.notch_sos, filtered, axis=0, zi=self.notch_zi)

        frontal = (filtered[:, self.fp1_idx] + filtered[:, self.fp2_idx]) / 2.0

        # --- IMPROVEMENT: Calculate threshold using history BEFORE rolling in the new raw chunk ---
        median = np.median(self.frontal_buffer)
        mad = np.median(np.abs(self.frontal_buffer - median))
        threshold = max(MIN_THRESHOLD, MAD_MULTIPLIER * 1.4826 * mad)

        # Roll the buffer forward now
        self.frontal_buffer = np.roll(self.frontal_buffer, -len(frontal))
        self.frontal_buffer[-len(frontal):] = frontal

        # Look for peaks only over the entire updated buffer
        peaks, _ = find_peaks(
            np.abs(self.frontal_buffer),
            height=threshold,
            prominence=threshold * 0.7,
            distance=self.min_distance
        )

        chunk_start = self.global_sample
        chunk_end = chunk_start + len(chunk)
        buffer_start = self.global_sample + len(frontal) - self.buffer_size

        cleaned = filtered.copy()
        blink_count = 0
        blink_times = []

        for peak in peaks:
            global_peak = buffer_start + peak

            if global_peak <= self.last_blink_sample:
                continue
            if not (chunk_start <= global_peak < chunk_end):
                continue

            self.last_blink_sample = global_peak + self.min_distance
            blink_count += 1
            blink_times.append(global_peak / self.fs)

            local_peak = global_peak - chunk_start
            start = max(0, local_peak - self.blink_window)
            end = min(len(chunk), local_peak + self.blink_window)

            for ch in [self.fp1_idx, self.fp2_idx]:
                cleaned[start:end, ch] = np.nan

        for ch in [self.fp1_idx, self.fp2_idx]:
            signal = cleaned[:, ch]
            valid = ~np.isnan(signal)
            if 0 < valid.sum() < len(signal):
                signal[~valid] = np.interp(
                    np.flatnonzero(~valid),
                    np.flatnonzero(valid),
                    signal[valid]
                )
            elif valid.sum() == 0:
                signal[:] = 0.0

        self.global_sample += len(chunk)
        return cleaned, blink_count, threshold, blink_times