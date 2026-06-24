# Nurolab System Architecture

## Overview

Nurolab is an EEG Analytics & Visualization Platform designed to process, analyze, visualize, and interpret electroencephalography (EEG) data. The current version operates on public EEG datasets and is designed to support future integration with real EEG acquisition hardware.

---

# Current Architecture (Dataset-Based)

```text
EEG Dataset
    ↓
Data Loader
    ↓
Preprocessing Pipeline
    ↓
Feature Extraction
    ↓
Analytics Engine
    ↓
Visualization Dashboard
    ↓
Reports & Exports
```

---

# Functional Layers

## 1. Data Layer

Responsible for storing and managing EEG datasets.

### Inputs

* EDF files
* CSV files
* Public EEG datasets
* Research datasets

### Responsibilities

* Dataset management
* Metadata storage
* Dataset versioning

---

## 2. Processing Layer

Responsible for preparing EEG signals for analysis.

### Components

* Notch Filtering
* Bandpass Filtering
* Signal Segmentation
* Normalization

### Outputs

* Clean EEG signals
* Segmented EEG windows

---

## 3. Analytics Layer

Responsible for extracting meaningful information.

### Features

* Delta Band Power
* Theta Band Power
* Alpha Band Power
* Beta Band Power

### Metrics

* Alpha/Beta Ratio
* Relaxation Index
* Engagement Index
* Signal Quality Score

---

## 4. Visualization Layer

Provides interactive visual representations.

### Components

* EEG Waveform Viewer
* Frequency Spectrum
* Session Analytics
* Trend Charts

---

## 5. Reporting Layer

Generates research and user reports.

### Outputs

* PDF Reports
* CSV Exports
* Session Summaries

---

# Future Hardware Architecture

The software architecture is designed to support future real-time EEG acquisition.

```text
EEG Headband
      ↓
ADS1299 Signal Acquisition
      ↓
ESP32 Edge Processing
      ↓
Secure Wireless Upload
      ↓
Cloud API Gateway
      ↓
Database & Storage
      ↓
Analytics Engine
      ↓
Dashboard & Reports
```

---

# Design Principles

* Modular architecture
* Hardware-independent design
* Cloud-ready deployment
* Research-focused workflows
* Scalable analytics pipeline

---

# Future Enhancements

* Real-time EEG streaming
* Edge AI inference
* Multi-user support
* Stress prediction
* Attention monitoring
* Sleep analytics
* Mobile application support
