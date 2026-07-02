# NuroLab — Architecture Guide

This document explains *why* the codebase is shaped the way it is. It is designed to help new contributors understand the design without reverse-engineering the system.

## Table of contents

- [Core design idea](#core-design-idea)
- [Signal journey](#signal-journey)
- [Pipeline consumers](#pipeline-consumers)
- [App-facing layer](#app-facing-layer)
- [Why the data contract matters](#why-the-data-contract-matters)
- [Recommended reading order](#recommended-reading-order)

---

## Core design idea

**EEG data and the code that processes it are kept strictly separate.**

Every data source — research datasets, synthetic test data, or future hardware — implements the same four-method interface in `datasources/base.py`. Every other file in the pipeline calls only those four methods and never cares where the bytes came from.

This separation is the single decision that makes the codebase easy to extend and reason about.

### Why it matters

- You can develop and test the full pipeline without real EEG data by using `SyntheticEEGSource`.
- When real hardware is available, one new adapter file plugs in and nothing else changes.
- Bugs are isolated. If windowing is broken, you fix it once in `processing/windowing.py`, not once per dataset format.

> If you are about to write code that special-cases “if this is a BDF file…” outside `datasources/`, stop. That logic belongs in a new adapter.

---

## Signal journey

EEG data moves through six labeled stages (A through F). Each stage is one file, does one job, and hands off clean output to the next.

```text
Raw chunk → Blink removal → Stage A (filter) → Stage B (window) → Stage C–E (features) → Stage F (select + scale) → Model / Deviation
```

### Blink removal — `data/processing/blink_remover.py`

`OnlineBlinkRemover` removes eye blink artifacts from frontal channels (Fp1, Fp2).

- Detects spikes using a **MAD (median absolute deviation)** threshold.
- Replaces artifact segments with linear interpolation.
- Keeps downstream filters from being poisoned by large transients.

**Why MAD?** A per-session threshold adapts to each subject’s signal level and is more robust than a fixed voltage threshold.

### Stage A — `processing/filters.py`

The filter pipeline applies two stages:

1. **Butterworth bandpass (0.1–70 Hz)** — preserves brain-relevant frequencies.
2. **Notch filter (50 or 60 Hz)** — removes mains interference.

Both filters use `sosfiltfilt` / `filtfilt` for **zero phase distortion**, which is critical because later stages measure timing and waveform shape.

### Stage B — `processing/windowing.py`

`SlidingWindowEngine` converts the EEG stream into fixed-length windows.

- Default window length: 20 seconds.
- Default stride: 2 seconds.
- Result: 18 seconds overlap and a new estimate every 2 seconds.

This class is source-agnostic and works with finite files or infinite live streams.

### Stage C–E — `processing/features.py`

For each channel and each of the 5 EEG bands (delta, theta, alpha, beta, gamma), the code computes:

- **PSD (Power Spectral Density)** via Welch’s method.
- **DE (Differential Entropy)** = `ln(PSD)`.
- **Hjorth parameters**: activity, mobility, complexity.

Features are named via `build_feature_names`, e.g. `Fp1_alpha_DE`.

### Stage F — `processing/feature_selection.py` + `sklearn.Pipeline`

Feature selection is essential when there are hundreds of features per window.

- Use `anova_select` or `SelectFpr` to remove noisy features.
- Keep selection and scaling inside a pipeline.
- This prevents data leakage during cross-validation.

> Read `docs/AVOIDING_DATA_LEAKAGE.md` before training any model.

---

## Pipeline consumers

### `ml/` — trained condition classifiers

Trained models are saved as `sklearn.Pipeline` objects that bundle selection, scaling, and classification. `ModelRegistry` loads them and exposes `predict_all()` so the server remains condition-agnostic.

### `processing/deviation_engine.py` — personal baseline detection

`DeviationEngine` compares current windows to a user-specific relaxed baseline.

- Uses Mahalanobis distance to account for correlated features.
- Uses CUSUM to detect sustained drift.
- Works without labeled training data.

This supports the “personal baseline” feature in the product plan.

---

## App-facing layer

`app_backend/server.py` exposes a FastAPI WebSocket endpoint.
It owns the live loop:

1. Pull a window.
2. Run the pipeline.
3. Run ML inference.
4. Run deviation tracking.
5. Send a JSON payload.

`app_backend/privacy_safeguards.py` enforces privacy principles in code:

- Minimum events before insights are generated.
- Coarse time-of-day buckets instead of exact timestamps.
- Only aggregate statistics are returned.

> This is the data-layer guarantee that prevents accidental exposure of identifying details.

---

## Why the data contract matters

Skipping the data contract introduces three major problems:

1. **No offline testing without real data.** Synthetic sources let you validate the pipeline before datasets or hardware exist.
2. **Duplicate pipelines for every format.** Without adapters, each dataset becomes a separate maintenance burden.
3. **Hardware integration becomes a research project.** `datasources/live_hardware.py` is designed so only one file changes when hardware is ready.

---

## Recommended reading order

1. `datasources/base.py` — the four-method contract.
2. `datasources/replay_source.py` — `SyntheticEEGSource` for local testing.
3. `processing/filters.py` → `windowing.py` → `features.py`.
4. `processing/feature_selection.py` + `docs/AVOIDING_DATA_LEAKAGE.md`.
5. `main.py` — how the pipeline is wired end to end.
6. `ml/train_depression.py` — a full training example.
7. `app_backend/server.py` — how the trained pipeline serves live data.

Then read `CONTRIBUTING.md` for where to add your work.
