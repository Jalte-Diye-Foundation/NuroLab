import numpy as np
import pandas as pd
import mne

from pathlib import Path
from scipy.signal import (
    butter,
    sosfilt,
    sosfilt_zi,
    iirnotch,
    tf2sos,
    find_peaks
)

# ==========================================================
# CONFIGURATION
# All tunable parameters are defined here in one place.
# Change these values to adjust pipeline behavior globally.
# ==========================================================

# Folder containing .bdf EEG files (and optional .tsv sidecars)
DATA_DIR = Path("data")

# Number of samples per chunk (512 samples = 1 second at 512 Hz)
CHUNK_SIZE = 512

# Bandpass filter cutoff frequencies (Hz)
# Keeps frequencies between 0.5 Hz and 15 Hz
# - 0.5 Hz lower cutoff removes slow DC drift
# - 15 Hz upper cutoff removes high-frequency noise
#   (blink artifacts are typically below 10 Hz, so this is safe)
BANDPASS_LOW  = 0.5
BANDPASS_HIGH = 15.0

# Notch filter to remove power line interference (50 Hz in Europe/India)
# Q factor controls the width of the notch — higher Q = narrower notch
NOTCH_FREQ = 50.0
NOTCH_Q    = 30

# Rolling buffer duration (seconds) used for adaptive threshold estimation
# Longer buffer = more stable threshold but slower adaptation to signal changes
BUFFER_SECONDS = 4.0

# Minimum time gap between two consecutive blinks (ms)
# Prevents the same blink from being detected multiple times
MIN_BLINK_DISTANCE_MS = 400

# Half-width of the artifact removal window around each detected blink peak (ms)
# Total window removed = 2 x BLINK_WINDOW_MS = 400 ms
BLINK_WINDOW_MS = 200

# Absolute minimum threshold (Volts) for blink detection
# Ensures the detector doesn't trigger on tiny noise when the signal is very quiet
MIN_THRESHOLD = 80e-6   # 80 µV

# Multiplier for the MAD-based adaptive threshold
# threshold = max(MIN_THRESHOLD, MAD_MULTIPLIER * 1.4826 * MAD)
# 1.4826 is the standard consistency factor that makes MAD equivalent
# to standard deviation for normally distributed data
MAD_MULTIPLIER = 6.0


# ==========================================================
# STREAM SOURCE
# Reads all BDF files from DATA_DIR one by one and yields
# data in fixed-size chunks to simulate a live device stream.
#
# Also loads optional BIDS sidecar files per recording:
#   _events.tsv   -> stimulus/event markers with onset times
#   _channels.tsv -> channel metadata (type, unit, etc.)
#
# Each yielded item is a (meta, chunk) tuple:
#   meta  -> dict with file info, timing, and events for this chunk
#   chunk -> np.ndarray of shape (chunk_size, n_channels)
#
# The processor downstream receives only (meta, chunk) —
# it has no knowledge of files, paths, or how data was loaded.
# To switch to a live device (LSL, socket, serial), replace
# only this function. The processor stays untouched.
# ==========================================================

def bdf_stream_source(chunk_size=CHUNK_SIZE):

    # Find and sort all BDF files in the data directory
    bdf_files = sorted(DATA_DIR.glob("*.bdf"))

    if not bdf_files:
        raise FileNotFoundError(
            f"No .bdf files found in:\n{DATA_DIR.resolve()}"
        )

    for file_path in bdf_files:

        print("\n" + "=" * 60)
        print(f"Loading: {file_path.name}")
        print("=" * 60)

        # Load the BDF file and keep only EEG channels
        raw = mne.io.read_raw_bdf(
            file_path,
            preload=True,
            verbose=False
        )
        raw.pick("eeg")

        # data shape: (n_samples, n_channels) after transpose
        data           = raw.get_data().T
        fs             = int(raw.info["sfreq"])
        channel_names  = raw.ch_names

        print(f"Sampling rate : {fs} Hz")
        print(f"Channels      : {len(channel_names)}")
        print(f"Duration      : {len(data) / fs:.2f} s")

        # Build a case-insensitive, space-stripped channel lookup
        # so "Fp1", "FP1", "fp 1" all resolve correctly
        channel_lookup = {
            ch.upper().replace(" ", ""): idx
            for idx, ch in enumerate(channel_names)
        }

        fp1_idx = channel_lookup.get("FP1")
        fp2_idx = channel_lookup.get("FP2")

        if fp1_idx is None or fp2_idx is None:
            raise ValueError(
                f"Fp1/Fp2 not found in {file_path.name}"
            )

        print(f"Fp1 index: {fp1_idx}")
        print(f"Fp2 index: {fp2_idx}")

        # ----------------------------------------------------------
        # Load optional BIDS sidecar files
        # These are matched by stripping "_eeg.bdf" from the filename
        # e.g. "sub-hc1_ses-hc_task-rest_eeg.bdf"
        #   -> "sub-hc1_ses-hc_task-rest_events.tsv"
        #   -> "sub-hc1_ses-hc_task-rest_channels.tsv"
        # ----------------------------------------------------------

        stem          = file_path.name.replace("_eeg.bdf", "")
        events_path   = DATA_DIR / f"{stem}_events.tsv"
        channels_path = DATA_DIR / f"{stem}_channels.tsv"

        events_df   = None
        channels_df = None

        if events_path.exists():
            events_df = pd.read_csv(events_path, sep="\t")
            print(f"Loaded events         : {len(events_df)}")
            print(f"Event columns         : {events_df.columns.tolist()}")

            # 'onset' column (in seconds) is required for chunk-level matching
            if "onset" not in events_df.columns:
                raise ValueError(
                    f"'onset' column missing in {events_path.name}"
                )
        else:
            print("No events.tsv found.")

        if channels_path.exists():
            channels_df = pd.read_csv(channels_path, sep="\t")
            print(f"Loaded channel metadata: {len(channels_df)}")
        else:
            print("No channels.tsv found.")

        # ----------------------------------------------------------
        # Yield data chunk by chunk
        # Each chunk carries its own metadata so the processor
        # always knows the temporal context of the data it receives
        # ----------------------------------------------------------

        total_samples = len(data)

        for start in range(0, total_samples, chunk_size):

            end = min(start + chunk_size, total_samples)

            # Wall-clock time range this chunk covers (in seconds)
            chunk_start_time = start / fs
            chunk_end_time   = end   / fs

            # Find any events whose onset falls within this chunk's time window
            chunk_events = []
            if events_df is not None:
                mask = (
                    (events_df["onset"] >= chunk_start_time) &
                    (events_df["onset"] <  chunk_end_time)
                )
                chunk_events = events_df.loc[mask].to_dict("records")

            meta = {
                "file_name"        : file_path.name,
                "new_file"         : start == 0,      # True only for the first chunk of each file
                "fs"               : fs,
                "n_channels"       : data.shape[1],
                "fp1_idx"          : fp1_idx,
                "fp2_idx"          : fp2_idx,
                "channel_info"     : channels_df,      # Full channel metadata table (or None)
                "chunk_start_time" : chunk_start_time,
                "chunk_end_time"   : chunk_end_time,
                "chunk_events"     : chunk_events      # List of event dicts in this chunk
            }

            yield meta, data[start:end]


# ==========================================================
# ONLINE BLINK REMOVER
# A stateful chunk-by-chunk processor. Receives one chunk
# at a time, filters it, detects blinks, removes artifacts,
# and returns a cleaned chunk of the same shape.
#
# Designed to be completely source-agnostic — it only sees
# (chunk, meta) and never interacts with files or I/O.
# ==========================================================

class OnlineBlinkRemover:

    def __init__(self, fs, n_channels, fp1_idx, fp2_idx):
        """
        Initializes filters and state variables for one recording session.
        Called once per BDF file (processor resets between files).

        Parameters
        ----------
        fs         : int   - Sampling rate in Hz
        n_channels : int   - Total number of EEG channels
        fp1_idx    : int   - Column index of Fp1 in the data array
        fp2_idx    : int   - Column index of Fp2 in the data array
        """

        self.fs          = fs
        self.n_channels  = n_channels
        self.fp1_idx     = fp1_idx
        self.fp2_idx     = fp2_idx

        # ----------------------------------------------------------
        # Filter design
        # Both filters are designed once and reused across all chunks.
        # Using second-order sections (SOS) format for numerical stability.
        # ----------------------------------------------------------

        # 4th-order Butterworth bandpass: 0.5 – 15 Hz
        self.bandpass_sos = butter(
            4,
            [BANDPASS_LOW, BANDPASS_HIGH],
            btype="bandpass",
            fs=fs,
            output="sos"
        )

        # Notch filter at 50 Hz to suppress power line noise
        b_notch, a_notch  = iirnotch(w0=NOTCH_FREQ, Q=NOTCH_Q, fs=fs)
        self.notch_sos     = tf2sos(b_notch, a_notch)

        # ----------------------------------------------------------
        # Filter initial conditions (zi)
        # These carry the filter state across chunk boundaries,
        # preventing discontinuities at chunk edges.
        # Shape: (n_sections, 2, n_channels)
        # ----------------------------------------------------------

        self.bp_zi    = np.repeat(
            sosfilt_zi(self.bandpass_sos)[:, :, np.newaxis],
            n_channels, axis=2
        )
        self.notch_zi = np.repeat(
            sosfilt_zi(self.notch_sos)[:, :, np.newaxis],
            n_channels, axis=2
        )

        # ----------------------------------------------------------
        # Rolling frontal buffer for adaptive threshold estimation
        # Stores the last BUFFER_SECONDS of the frontal signal
        # (average of Fp1 and Fp2) to compute a running MAD threshold
        # ----------------------------------------------------------

        self.buffer_size    = int(BUFFER_SECONDS * fs)
        self.frontal_buffer = np.zeros(self.buffer_size)

        # ----------------------------------------------------------
        # Sample counters and blink state tracking
        # ----------------------------------------------------------

        # Tracks the absolute sample index across all chunks
        self.global_sample = 0

        # Absolute sample index of the last detected blink peak
        # Initialized far in the past so the first blink is never suppressed
        self.last_blink_sample = -100000

        # Minimum sample gap between two blink detections (refractory period)
        self.min_distance = int(MIN_BLINK_DISTANCE_MS * fs / 1000)

        # Half-width of the artifact removal window in samples
        self.blink_window = int(BLINK_WINDOW_MS * fs / 1000)


    def process(self, chunk):
        """
        Processes a single chunk of EEG data.

        Steps:
          1. Bandpass filter  (all channels, stateful)
          2. Notch filter     (all channels, stateful)
          3. Update frontal buffer with average of Fp1 + Fp2
          4. Compute adaptive MAD-based detection threshold
          5. Detect blink peaks in the frontal buffer
          6. For each valid blink: mark window as NaN on Fp1 & Fp2
          7. Interpolate NaN regions linearly on Fp1 & Fp2
          8. Return cleaned chunk + detection metadata

        Parameters
        ----------
        chunk : np.ndarray, shape (n_samples, n_channels)

        Returns
        -------
        cleaned     : np.ndarray, shape (n_samples, n_channels)
                      Filtered data with blink artifacts removed on Fp1/Fp2.
                      All other channels are returned filtered but uncorrected.
        blink_count : int    - Number of blinks detected in this chunk
        threshold   : float  - Detection threshold used (in Volts)
        blink_times : list   - Timestamps (seconds) of detected blinks
        """

        # ----------------------------------------------------------
        # Step 1 & 2: Apply bandpass then notch filter
        # sosfilt returns both the filtered signal and the updated
        # filter state (zi), which is saved for the next chunk
        # ----------------------------------------------------------

        filtered, self.bp_zi    = sosfilt(
            self.bandpass_sos, chunk, axis=0, zi=self.bp_zi
        )
        filtered, self.notch_zi = sosfilt(
            self.notch_sos, filtered, axis=0, zi=self.notch_zi
        )

        # ----------------------------------------------------------
        # Step 3: Update frontal buffer
        # Average Fp1 and Fp2 to get a single frontal EOG-like signal.
        # Roll the buffer left by chunk length, then fill the tail.
        # ----------------------------------------------------------

        frontal = (filtered[:, self.fp1_idx] + filtered[:, self.fp2_idx]) / 2

        self.frontal_buffer = np.roll(self.frontal_buffer, -len(frontal))
        self.frontal_buffer[-len(frontal):] = frontal

        # ----------------------------------------------------------
        # Step 4: Compute adaptive MAD-based threshold
        # MAD (Median Absolute Deviation) is robust to outliers,
        # making it suitable for signals that contain occasional
        # large-amplitude blink artifacts.
        #
        # threshold = max(MIN_THRESHOLD, MAD_MULTIPLIER * 1.4826 * MAD)
        # ----------------------------------------------------------

        median    = np.median(self.frontal_buffer)
        mad       = np.median(np.abs(self.frontal_buffer - median))
        threshold = max(MIN_THRESHOLD, MAD_MULTIPLIER * 1.4826 * mad)

        # ----------------------------------------------------------
        # Step 5: Detect peaks in the absolute frontal signal
        # Peaks must exceed the threshold in both height and prominence,
        # and must be separated by at least min_distance samples.
        # ----------------------------------------------------------

        peaks, _ = find_peaks(
            np.abs(self.frontal_buffer),
            height     = threshold,
            prominence = threshold * 0.7,   # avoids detecting shoulders of large blinks
            distance   = self.min_distance
        )

        # Map chunk boundaries to global sample indices
        chunk_start = self.global_sample
        chunk_end   = chunk_start + len(chunk)

        cleaned     = filtered.copy()
        blink_count = 0
        blink_times = []

        # ----------------------------------------------------------
        # Step 6: Process each detected peak
        # Peaks are found in the rolling buffer (global context),
        # but we only act on peaks that fall within the current chunk.
        # ----------------------------------------------------------

        for peak in peaks:

            # Convert buffer-relative peak index to global sample index
            # (the buffer's last sample corresponds to global_sample - 1)
            global_peak = self.global_sample - len(frontal) + peak

            # Skip if this peak was already counted in a previous chunk
            if global_peak <= self.last_blink_sample:
                continue

            # Skip if this peak doesn't belong to the current chunk
            if not (chunk_start <= global_peak < chunk_end):
                continue

            # Update refractory period: suppress detections too close to this blink
            self.last_blink_sample = global_peak + self.min_distance

            blink_count += 1
            blink_time   = global_peak / self.fs
            blink_times.append(blink_time)

            # Convert global peak index to local index within this chunk
            local_peak = global_peak - chunk_start

            # Define the artifact removal window (clamped to chunk boundaries)
            start = max(0,          local_peak - self.blink_window)
            end   = min(len(chunk), local_peak + self.blink_window)

            # Mark the blink window as NaN on frontal channels only
            # Other channels are unaffected
            for ch in [self.fp1_idx, self.fp2_idx]:
                cleaned[start:end, ch] = np.nan

        # ----------------------------------------------------------
        # Step 7: Interpolate NaN regions on Fp1 and Fp2
        # Linear interpolation bridges the gap left by removed blinks.
        # Edge case: if the entire chunk is NaN, fill with zeros.
        # ----------------------------------------------------------

        for ch in [self.fp1_idx, self.fp2_idx]:

            signal = cleaned[:, ch]
            valid  = ~np.isnan(signal)

            if valid.sum() > 1:
                # Interpolate only at NaN positions using valid surrounding samples
                signal[~valid] = np.interp(
                    np.flatnonzero(~valid),
                    np.flatnonzero(valid),
                    signal[valid]
                )
            elif valid.sum() == 0:
                # Entire chunk is NaN (very large or back-to-back blinks)
                signal[:] = 0.0

        # Advance global sample counter by the number of samples processed
        self.global_sample += len(chunk)

        return cleaned, blink_count, threshold, blink_times


# ==========================================================
# MAIN LOOP
# Drives the pipeline: pulls chunks from the source,
# feeds them to the processor, and prints per-chunk stats.
#
# Output stream (cleaned_chunk) is ready to be forwarded
# to a queue, file writer, or downstream analysis module.
# ==========================================================

if __name__ == "__main__":

    processor      = None
    total_blinks   = 0
    chunk_num      = 0
    all_blink_times = []

    for meta, raw_chunk in bdf_stream_source():

        # Reset the processor at the start of each new file
        # This clears filter state, buffers, and sample counters
        if meta["new_file"]:
            processor = OnlineBlinkRemover(
                fs         = meta["fs"],
                n_channels = meta["n_channels"],
                fp1_idx    = meta["fp1_idx"],
                fp2_idx    = meta["fp2_idx"]
            )
            print(f"\nStarted stream: {meta['file_name']}")

        chunk_num += 1

        cleaned_chunk, blink_count, threshold, blink_times = processor.process(raw_chunk)

        total_blinks += blink_count
        all_blink_times.extend(blink_times)

        # ---- OUTPUT STREAM ----
        # cleaned_chunk is ready to forward downstream
        # e.g. output_queue.put(cleaned_chunk)

        # Format blink times and event onsets for display
        blink_str = (
            ", ".join(f"{t:.2f}s" for t in blink_times)
            if blink_times else "-"
        )
        event_str = (
            ", ".join(f"{e['onset']:.2f}s" for e in meta["chunk_events"])
            if meta["chunk_events"] else "-"
        )

        print(
            f"Chunk {chunk_num:03d} | "
            f"{meta['chunk_start_time']:.2f}-{meta['chunk_end_time']:.2f}s | "
            f"Blinks: {blink_count:2d} [{blink_str}] | "
            f"Events: {len(meta['chunk_events']):2d} [{event_str}] | "
            f"Threshold: {threshold:.2e}"
        )

    print("\n" + "=" * 60)
    print("Stream processing complete.")
    print(f"Total blinks detected: {total_blinks}")
    print("\nDetected blink times:")
    print([round(t, 2) for t in all_blink_times])
    print("=" * 60)