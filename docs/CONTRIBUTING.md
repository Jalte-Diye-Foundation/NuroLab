# Contributing to NuroLab — Where to Plug In

This document is the practical companion to [`ARCHITECTURE.md`](./ARCHITECTURE.md).
Read that first for *why* the code is shaped this way. This document explains *where* to add your work and which files to touch.

## Quick start

1. Read `ARCHITECTURE.md` for the design intent.
2. Read `AVOIDING_DATA_LEAKAGE.md` before training or evaluating models.
3. Find the matching contribution section below and follow the file guidance.
4. Run tests and use the PR checklist before submitting.

## Table of contents

- [What to read first](#what-to-read-first)
- [Add a new neurological condition](#add-a-new-neurological-condition)
- [Add a new EEG feature](#add-a-new-eeg-feature)
- [Support a new EEG file format or dataset](#support-a-new-eeg-file-format-or-dataset)
- [Live hardware integration](#live-hardware-integration)
- [Personal calibration / baseline flow](#personal-calibration--baseline-flow)
- [Privacy and safety work](#privacy-and-safety-work)
- [Fixing core pipeline bugs](#fixing-core-pipeline-bugs)
- [PR checklist](#pr-checklist)

---

## What to read first

Start with:

1. `ARCHITECTURE.md` — for the design intent and data contract.
2. `AVOIDING_DATA_LEAKAGE.md` — for model training safety.
3. `CONTRIBUTING.md` — for the best place to add your work.

---

## Add a new neurological condition

This is the most common next task, and the architecture is built to make it cheap.

### What to change

1. **Find a labeled public dataset.** Check OpenNeuro, PhysioNet, and Kaggle first.
2. **Add a data adapter** if needed.
   - Copy `datasources/openneuro_depression.py` as a template.
   - Update how labels are derived from metadata.
3. **Add a training script.**
   - Copy `ml/train_depression.py`.
   - Change `BIDS_ROOT` and label-loading logic only.
   - Keep feature extraction, windowing, and `GroupKFold` the same.
4. **Register the model.**
   - Add one line to the `model_paths` dict in `app_backend/server.py`.

### Important constraints

- Do not add new filtering, windowing, or feature extraction code for a new condition.
- If you think condition-specific preprocessing is needed, discuss it first.
- Read `docs/AVOIDING_DATA_LEAKAGE.md` before running any training job.

---

## Add a new EEG feature

Edit `processing/features.py` only.

### New band

- Add the band to the `BANDS` dict.
- Everything downstream picks it up automatically.

### New feature type

- Implement a new feature function similar to `hjorth_parameters()` or `pli_matrix()`.
- Wire it into `extract_feature_vector()` and `build_feature_names()`.
- Always give each feature a human-readable name.

> Never add an unnamed feature. If you cannot map an index to a name, the feature becomes undebuggable.

---

## Support a new EEG file format or dataset

Add a new file under `datasources/`.

### Fastest path

1. Copy either `datasources/openneuro_depression.py` or `datasources/bonn_epilepsy.py`.
2. Implement the four required methods from `datasources/base.py`:
   - `sample_rate`
   - `channel_names`
   - `n_channels`
   - `read_chunk()`
   - `is_live()`
3. Test the adapter independently before using it in a training script.

### Test before wiring

Write a throwaway script that:

- creates the adapter,
- calls `read_chunk()` several times,
- verifies shapes and values look sane,
- then plugs it into `SlidingWindowEngine`.

---

## Live hardware integration

The hardware integration belongs in `datasources/live_hardware.py`.

### What you need from firmware/hardware

- Transport type: USB-Serial, BLE, or WiFi/WebSocket.
- Frame format: binary struct or CSV/JSON lines.
- Confirmed sample rate, channel count, and channel order.

### How to validate before hardware exists

Use `datasources/mock_serial_hardware.py` to test parsing logic with a fake serial port. That generator produces synthetic EEG-shaped CSV lines at the correct sample rate so the full chain can be validated without hardware.

> Nothing outside `datasources/live_hardware.py` should need to change when hardware becomes real.

---

## Personal calibration / baseline flow

This work is centered on `processing/deviation_engine.py` and the calibration endpoints in `app_backend/server.py`.

### What is already done

- The baseline math is implemented.
- The endpoints are sketched in the server.

### What is missing

- UX flow for collecting ~5 minutes of relaxed EEG.
- Converting that session into feature vectors.
- POSTing those vectors to `/calibration/build_baseline`.

This is primarily app/frontend work supported by the existing backend engine.

---

## Privacy and safety work

Read `app_backend/privacy_logger.py` and `app_backend/privacy_safeguards.py` carefully.
Every constraint maps to a privacy principle in the product plan.

### If you add new insights or aggregates

- Route them through `PrivacySafeguardsEngine.get_insight()`.
- Do not read directly from per-event stores.

That central path enforces minimum-sample-size gating and prevents accidental bypass of privacy checks.

---

## Fixing core pipeline bugs

The shared pipeline files are heavily used by every condition and every model.

### Before changing behavior

1. Write a failing test in `tests/test_pipeline.py`.
2. Fix the bug.
3. Confirm the test passes and `pytest nurolab/tests/ -v` is still green.

### Why this is important

A silent behavior change in `processing/filters.py`, `processing/windowing.py`, or `processing/features.py` can corrupt every condition at once without a visible symptom.
Treat changes here with more caution than changes anywhere else.

---

## PR checklist

- [ ] Did you run `pytest nurolab/tests/ -v` and confirm everything passes?
- [ ] If you touched `processing/`, did you add or update a test in `tests/test_pipeline.py`?
- [ ] If you trained a new model, did you use `GroupKFold` with subject IDs and feature selection inside an `sklearn.Pipeline`?
- [ ] Does your code avoid hardcoded absolute paths? Use `Path(__file__).resolve().parent...` patterns.
- [ ] If you added a new feature, is it named in `build_feature_names()` so it stays interpretable end-to-end?
