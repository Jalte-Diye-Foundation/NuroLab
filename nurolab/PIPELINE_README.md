# NuroLab — EEG Pipeline & ML Backend

> Part of the [Jalte Diye Foundation](https://reallyrealeducation.org/Nurolab.html) NuroLab initiative —
> Smart Mental Health Monitoring using EEG & Artificial Intelligence.

This folder contains the **technical implementation** of the NuroLab signal processing
and machine learning pipeline. For the project vision, research plan, and roadmap, see
the [`docs/`](./docs/) folder.

---

## What this pipeline does

Raw EEG data streams in 512-sample chunks through:

1. **Blink artifact removal** — MAD-based adaptive threshold, linear interpolation
2. **Stage A filters** — zero-phase Butterworth bandpass + 50 Hz notch
3. **Sliding window engine** — 20-second windows, 2-second stride
4. **Feature extraction** — 320 features per window (Differential Entropy, PSD, Hjorth across 5 EEG bands × 40 channels)
5. **ML classification** — Linear SVM trained on OpenNeuro ds003478 (depression) and Bonn epilepsy dataset
6. **FastAPI WebSocket server** — streams JSON to the Android app every 2 seconds

**Current status:** Pipeline running on real EEG data — 51 blinks detected, 87 windows, 320 features per window. Depression classifier trained (GroupKFold subject-wise CV, no data leakage). FastAPI server scaffolded.

---

## Quickstart (any PC)

### 1. Clone and install
```bash
git clone https://github.com/Jalte-Diye-Foundation/NuroLab.git
cd NuroLab
pip install -r requirements.txt
```

### 2. Test immediately — no data needed
```bash
python -m nurolab.main --synthetic
```

### 3. Run on real EEG data
Place your `.bdf` file in `data/` then:
```bash
python -m nurolab.main
```

### 4. Start the API server
```bash
pip install fastapi uvicorn
uvicorn nurolab.app_backend.server:app --reload --port 8000
```

---

## Project structure

```
NuroLab/
  nurolab/                  ← Python package (the pipeline)
    datasources/            ← Data adapters (BDF, .set, synthetic, live hardware)
    processing/             ← Filters, windowing, features, deviation engine
    ml/                     ← Model training scripts + model registry
    app_backend/            ← FastAPI WebSocket server + privacy safeguards
    tests/                  ← Test suite
    main.py                 ← Entry point
  data/                     ← Your EEG files go here (gitignored)
    processing/
      blink_remover.py      ← Artifact removal (original implementation)
    features/
      extractor.py          ← Feature extraction (original implementation)
  models/                   ← Trained .pkl models saved here (gitignored)
  docs/                     ← Project documentation
  requirements.txt
```

---

## Documentation

| Document | What it covers |
|---|---|
| [`docs/roadmap.md`](./docs/roadmap.md) | Project milestones and timeline |
| [`docs/architecture.md`](./docs/architecture.md) | System architecture overview |
| [`docs/datasets.md`](./docs/datasets.md) | Dataset sources and descriptions |
| [`docs/research-plan.md`](./docs/research-plan.md) | Research methodology |
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | **Technical pipeline architecture** — read before touching code |
| [`docs/CONTRIBUTING.md`](./docs/CONTRIBUTING.md) | **Where to plug in** — add conditions, features, hardware |
| [`docs/AVOIDING_DATA_LEAKAGE.md`](./docs/AVOIDING_DATA_LEAKAGE.md) | **Required reading** before training any model |

---

## Data setup

Data files are not included in this repo (size + OpenNeuro license).

**Depression dataset (ds003478):**
Download from https://openneuro.org/datasets/ds003478/versions/1.1.0
Place under `data/ds003478/` then run:
```bash
python -m nurolab.ml.train_depression
```

**Epilepsy dataset (Bonn):**
Download from https://www.kaggle.com/datasets/harunshimanto/epileptic-seizure-recognition
Place under `data/bonn_eeg/A/`, `B/`, `C/`, `D/`, `E/` then run:
```bash
python -m nurolab.ml.train_epilepsy
```

---

## Disclaimer

NuroLab is a research and technology initiative. It is not intended to diagnose,
treat, cure, or prevent any medical or psychiatric condition. Any insights generated
by the system should be interpreted in conjunction with professional clinical
assessment and established scientific evidence.
