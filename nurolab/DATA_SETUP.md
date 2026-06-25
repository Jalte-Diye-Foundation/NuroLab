# NuroLab — Data Setup Guide

## Step 1 — Your existing BDF file (run immediately)

Move your file so the path is exactly:
```
nurolab\data\sub-hc1_ses-hc_task-rest_eeg.bdf
```
Then run:
```bash
python -m nurolab.main
```

---

## Step 2 — Depression dataset (ds003478) — for ML training

**Direct link:** https://openneuro.org/datasets/ds003478/versions/1.1.0

### What to download (do NOT download all 122 subjects — start with 10)

On the OpenNeuro page, click individual files:

**Must download (root level):**
- `participants.tsv` — has BDI scores (depression labels)

**Download these 10 subject folders** (5 depressed BDI≥13, 5 control BDI<7):
```
sub-001/eeg/sub-001_task-rest_eeg.set
sub-001/eeg/sub-001_task-rest_eeg.fdt   ← companion file, required with .set
sub-002/eeg/sub-002_task-rest_eeg.set
sub-002/eeg/sub-002_task-rest_eeg.fdt
... (repeat for sub-003 through sub-010)
```

### Where to put them:
```
nurolab\
  data\
    sub-hc1_ses-hc_task-rest_eeg.bdf    ← your existing file
    ds003478\
      participants.tsv                   ← REQUIRED: has BDI labels
      sub-001\
        eeg\
          sub-001_task-rest_eeg.set
          sub-001_task-rest_eeg.fdt
      sub-002\
        eeg\
          sub-002_task-rest_eeg.set
          sub-002_task-rest_eeg.fdt
      (... sub-003 to sub-010)
```

### Then run:
```bash
python -m nurolab.ml.train_depression
```

---

## Step 3 — Epilepsy dataset (Bonn) — for ML training

**Direct Kaggle link:** https://www.kaggle.com/datasets/harunshimanto/epileptic-seizure-recognition

OR download directly from the university mirror:
http://epileptologie-bonn.de/cms/front_content.php?idcat=193&lang=3

### What to download:
5 zip files: A.zip, B.zip, C.zip, D.zip, E.zip (each ~2 MB, total ~10 MB)

### Where to put them (unzip into):
```
nurolab\
  data\
    bonn_eeg\
      A\
        A001.txt
        A002.txt
        ... (100 files)
      B\
        B001.txt
        ...
      C\  D\  E\  (same structure)
```

### Then run:
```bash
python -m nurolab.ml.train_epilepsy
```

---

## Quick test (no downloads needed):
```bash
python -m nurolab.main --synthetic    # already works!
```
