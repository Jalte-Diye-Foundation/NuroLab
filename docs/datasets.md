# EEG Datasets

## Overview

This document describes datasets used by Nurolab for research, development, testing, and machine learning experiments.

---

# Dataset Requirements

Preferred datasets should include:

* Multi-channel EEG recordings
* Sampling frequency information
* Session metadata
* Participant information (anonymized)
* Research labels when available

---

# Recommended Public Datasets

## EEG Motor Movement/Imagery Dataset

Source:
PhysioNet

Applications:

* Motor imagery classification
* Feature extraction
* Signal processing experiments

---

## TUH EEG Corpus

Source:
Temple University Hospital

Applications:

* Large-scale EEG analysis
* Abnormal EEG detection
* Machine learning research

---

## CHB-MIT Scalp EEG Database

Source:
PhysioNet

Applications:

* Seizure detection research
* Event detection
* Time-series analysis

---

## DEAP Dataset

Applications:

* Emotion recognition
* Affective computing
* EEG classification experiments

---

## SEED Dataset

Applications:

* Emotion analysis
* Cognitive state prediction
* Machine learning benchmarks

---

# Directory Structure

```text
data/
├── raw/
├── processed/
├── features/
├── labels/
└── exports/
```

---

# Dataset Processing Workflow

```text
Raw Dataset
      ↓
Validation
      ↓
Preprocessing
      ↓
Feature Extraction
      ↓
Analytics
      ↓
Model Training
```

---

# Metadata Standards

Each dataset should contain:

| Field         | Description               |
| ------------- | ------------------------- |
| dataset_id    | Unique dataset identifier |
| subject_id    | Participant identifier    |
| session_id    | Recording session         |
| sampling_rate | EEG sampling frequency    |
| channels      | Number of EEG channels    |
| duration      | Recording duration        |
| labels        | Optional class labels     |

---

# Storage Guidelines

## Raw Data

Store original files unchanged.

Location:

```text
data/raw/
```

## Processed Data

Store filtered and cleaned EEG data.

Location:

```text
data/processed/
```

## Features

Store extracted feature matrices.

Location:

```text
data/features/
```

---

# Future Dataset Collection

When hardware becomes available:

* Collect proprietary EEG recordings
* Build labeled research datasets
* Develop longitudinal studies
* Create domain-specific benchmarks

---

# Ethical Considerations

* No personally identifiable information
* Participant consent required
* Follow applicable research guidelines
* Maintain anonymized records
