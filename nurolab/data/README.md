# EEG Datasets — Metadata

## ds003478 — Depression Rest EEG (OpenNeuro)
- Source: https://openneuro.org/datasets/ds003478/versions/1.1.0
- Total dataset size: 122 subjects (full dataset on OpenNeuro)
- Subjects downloaded so far: 8 (sub-001, 002, 003, 004 = control; sub-052, 053, 055, 058 = depressed)
- Sampling rate: 500 Hz
- Channels: 66-67 (varies per subject)
- Labels: BDI score in participants.tsv (>=13 depressed, <7 control)
- Format: EEGLAB .set/.fdt

## sub-hc1_ses-hc_task-rest_eeg.bdf
- Source: OpenNeuro healthy control sample
- Sampling rate: 512 Hz
- Channels: 40
- Duration: 192 seconds
- Format: BioSemi BDF

## Epileptic Seizure Recognition (Kaggle, Bonn dataset reformatted)
- Source: https://www.kaggle.com/datasets/harunshimanto/epileptic-seizure-recognition
- Original source: University of Bonn (Andrzejak et al. 2001)
- Format: single CSV, 11,500 rows
- Each row: one 178-sample EEG segment (1 second at 178 Hz)
- Original 5-class labels collapsed to 3-class scheme:
  - y=1 (seizure) -> seizure
  - y=2,3 (tumor/abnormal area) -> interictal
  - y=4,5 (healthy, eyes open/closed) -> normal
- Class balance: 4600 normal, 4600 interictal, 2300 seizure