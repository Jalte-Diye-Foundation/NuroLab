"""
NuroLab — Main Pipeline Entry Point

Works on ANY PC — zero hardcoded paths.

Usage (from the project root folder):
    python -m nurolab.main                  # streams .bdf files from ./data/
    python -m nurolab.main --synthetic      # synthetic data, no files needed
    python -m nurolab.main --data-dir path  # custom data folder
"""

import argparse, sys
import numpy as np
from pathlib import Path

# Resolve project root from this file's location — works on any PC
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nurolab.datasources.openneuro_depression import OpenNeuroDepressionSource
from nurolab.datasources.replay_source import SyntheticEEGSource
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.windowing import SlidingWindowEngine
from nurolab.processing.features import extract_feature_vector, build_feature_names

# Blink remover lives in nurolab/data/processing/ (your original file)
_BLINK_PATH = PROJECT_ROOT / "nurolab" / "data" / "processing"
sys.path.insert(0, str(PROJECT_ROOT / "nurolab"))
from data.processing.blink_remover import OnlineBlinkRemover

CHUNK_SIZE = 512
WINDOW_SEC = 20.0
STRIDE_SEC = 2.0
NOTCH_FREQ = 50.0


def run_bdf_stream(data_dir: Path):
    bdf_files = sorted(data_dir.glob("*.bdf"))
    if not bdf_files:
        raise FileNotFoundError(
            f"No .bdf files found in {data_dir.resolve()}\n"
            f"Tip: run with --synthetic to test without data files."
        )

    total_blinks = total_windows = 0

    for bdf_path in bdf_files:
        print("\n" + "=" * 60)
        print(f"Loading: {bdf_path.name}")
        print("=" * 60)

        src  = OpenNeuroDepressionSource(str(bdf_path))
        fs   = src.sample_rate
        n_ch = src.n_channels
        print(f"Sampling rate : {fs:.0f} Hz | Channels: {n_ch} | Duration: {len(src._data)/fs:.1f}s")

        blink_remover  = OnlineBlinkRemover(fs=fs, n_channels=n_ch,
                                            fp1_idx=src.fp1_idx or 0,
                                            fp2_idx=src.fp2_idx or 1)
        feature_names  = build_feature_names(src.channel_names)
        cleaned_buffer = np.zeros((0, n_ch))
        stream_samples = 0
        win_samples    = int(WINDOW_SEC * fs)
        step_samples   = int(STRIDE_SEC * fs)
        file_blinks    = 0
        chunk_idx      = 0

        while True:
            raw_chunk = src.read_chunk(CHUNK_SIZE)
            if raw_chunk is None:
                break
            chunk_idx += 1
            cleaned_chunk, blink_count, threshold, blink_times = blink_remover.process(raw_chunk)
            file_blinks   += blink_count
            stream_samples += len(cleaned_chunk)

            blink_str = (f"{blink_count} [{', '.join(f'{t:.2f}s' for t in blink_times)}]"
                         if blink_times else f"{blink_count} [-]")
            print(f"Chunk {chunk_idx:4d} | "
                  f"{(stream_samples-len(cleaned_chunk))/fs:.2f}s–{stream_samples/fs:.2f}s | "
                  f"Blinks: {blink_str:22s} | Threshold: {threshold:.2e}")

            cleaned_buffer = np.vstack([cleaned_buffer, cleaned_chunk])

            while len(cleaned_buffer) >= win_samples:
                epoch      = cleaned_buffer[:win_samples, :]
                win_start  = (stream_samples - len(cleaned_buffer)) / fs
                win_end    = win_start + WINDOW_SEC
                filtered   = stage_a_pipeline(epoch, fs, notch_freq=NOTCH_FREQ)
                fv         = extract_feature_vector(filtered, fs)
                print(f"   [WINDOW ENGINE] {win_start:.1f}s–{win_end:.1f}s | "
                      f"Features: {len(fv)} | Ch0 Alpha DE: {fv[3]:.2f}")
                total_windows  += 1
                cleaned_buffer  = cleaned_buffer[step_samples:, :]

        total_blinks += file_blinks
        print(f"\n[{bdf_path.name}] Blinks: {file_blinks}")

    print("\n" + "=" * 60)
    print(f"Done. Blinks: {total_blinks} | Windows: {total_windows}")
    print("=" * 60)


def run_synthetic_stream():
    print("=" * 60)
    print("NuroLab — Synthetic EEG Stream (no data files needed)")
    print("=" * 60)
    src    = SyntheticEEGSource(n_channels=8, fs=256.0,
                                channel_names=["Fp1","Fp2","F3","F4","T7","T8","O1","O2"])
    engine = SlidingWindowEngine(src, window_sec=WINDOW_SEC, stride_sec=STRIDE_SEC)
    for i, (window, meta) in enumerate(engine.windows()):
        fv = extract_feature_vector(stage_a_pipeline(window, src.sample_rate), src.sample_rate)
        print(f"   [WINDOW ENGINE] {meta['window_start_time']:.1f}s–{meta['window_end_time']:.1f}s | "
              f"Features: {len(fv)} | Fp1 alpha DE: {fv[3]:.2f}")
        if i >= 9:
            print("... (stopping after 10 windows)")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NuroLab EEG pipeline")
    parser.add_argument("--synthetic", action="store_true",
                        help="Use synthetic data instead of .bdf files")
    parser.add_argument("--data-dir", default=str(PROJECT_ROOT / "nurolab" / "data"),
                        help="Folder containing .bdf files")
    args = parser.parse_args()

    if args.synthetic:
        run_synthetic_stream()
    else:
        run_bdf_stream(Path(args.data_dir))
