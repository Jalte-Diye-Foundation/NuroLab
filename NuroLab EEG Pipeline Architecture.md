# EEG-Based Real-Time Mental State Classification System

A real-time EEG signal processing and machine learning pipeline for classifying neural patterns associated with **Major Depressive Disorder (MDD)**, **Anxiety**, and **Epileptic Seizure Activity**. The architecture decouples raw signal processing from ML classification, grounding every decision in neurobiological evidence rather than a black-box model.

---

## Table of Contents

- [Overview](#overview)
- [Signal Processing Pipeline](#signal-processing-pipeline)
  - [Stage A: Temporal Filtering](#stage-a-temporal-filtering)
  - [Stage B: Window Partitioning](#stage-b-window-partitioning)
  - [Stage C: Spectral Transformation](#stage-c-spectral-transformation)
  - [Stage D: Brainwave Band Separation](#stage-d-brainwave-band-separation)
  - [Stage E: Dual-Domain Feature Extraction](#stage-e-dual-domain-feature-extraction)
  - [Stage F: Spatial Concatenation & Scaling](#stage-f-spatial-concatenation--scaling)
- [Real-Time Windowing Matrix](#real-time-windowing-matrix)
- [Neurobiological Classification Profiles](#neurobiological-classification-profiles)
- [Functional Connectivity Analysis](#functional-connectivity-analysis)
- [Personalized EEG Baseline Framework](#personalized-eeg-baseline-framework)
- [Deviation Detection Engine](#deviation-detection-engine)
- [Risk Indicator Framework](#risk-indicator-framework)
- [Trigger Detection & Closed-Loop Therapy](#trigger-detection--closed-loop-therapy)
- [Experimental Paradigms](#experimental-paradigms)
- [Classification Modeling](#classification-modeling)
- [References](#references)
---

## Overview

Raw EEG electrodes record voltage fluctuations from the scalp — signals contaminated by eye blinks, jaw movements, and 50 Hz AC electrical interference. Feeding this raw data directly into an ML model causes the model to learn noise patterns rather than true brain activity.

The solution is to transform data from the **Time Domain** (amplitude over time) into the **Frequency Domain** (energy volume at specific brainwave speeds), then extract structured, neurobiologically meaningful features.

```
[Raw Scalp Voltage]
        │
        ▼ Stage A: Temporal Filtering
[Butterworth Bandpass (0.1–70Hz) + Notch Filter (50Hz)]
        │
        ▼ Stage B: Window Partitioning
[20-Second Data Segment Matrix]
        │
        ▼ Stage C: Spectral Transformation
[Short-Time Fourier Transform (STFT) with Hanning Window]
        │
        ▼ Stage D: Brainwave Band Separation
[Power Spectral Density (PSD) for Delta, Theta, Alpha, Beta, Gamma]
        │
        ▼ Stage E: Dual-Domain Feature Extraction
[Differential Entropy (DE) via ln(PSD) + Hjorth Parameters]
        │
        ▼ Stage E (Filter): ANOVA Feature Selection
[One-Way ANOVA — discard features with p > 0.05]
        │
        ▼ Stage F: Spatial Concatenation & Scaling
[Normalized Multi-Channel Feature Vector]
```

---

## Signal Processing Pipeline

### Stage A: Temporal Filtering

Before any advanced computation, the raw signal is cleaned using two digital filters:

| Filter | Specification | Purpose |
|--------|--------------|---------|
| Butterworth Bandpass | 10th-order, 0.1–70 Hz | Blocks slow eye-drift artifacts (<0.1 Hz) and muscle tension noise (>70 Hz). A 10th-order setting gives an exceptionally sharp cut-off edge. |
| Notch Filter | 50 Hz | Eliminates AC power-line interference (India standard). Erases only the exact 50 Hz hum, leaving surrounding data intact. |

---

### Stage B: Window Partitioning

The continuous EEG stream is divided into **20-second rolling windows** using a sliding buffer:

- Every **2 seconds**, the oldest 2 seconds of data are dropped and replaced with the newest 2 seconds.
- This maintains a constant 20-second buffer ready for spectral analysis.

---

### Stage C: Spectral Transformation

A **Short-Time Fourier Transform (STFT)** identifies hidden frequency components within each 20-second window.

- A **1-second Hanning Window** (bell-shaped curve) is applied before the STFT to taper the edges of each data segment smoothly to zero, preventing spectral leakage from sharp discontinuities at chunk boundaries.
- A **512-point FFT** setting delivers high-resolution frequency mapping.

---

### Stage D: Brainwave Band Separation

The STFT output yields the **Power Spectral Density (PSD)** — the exact energy volume at every frequency bin. PSD values are then averaged into the 5 canonical neuroscientific brainwave bands:

| Band | Frequency Range | Cognitive Association |
|------|-----------------|-----------------------|
| **Delta** | 1–3 Hz | Deep sleep, unconscious processing |
| **Theta** | 4–7 Hz | Deep relaxation, light sleep, daydreaming |
| **Alpha** | 8–13 Hz | Calm, relaxed focus, alert baseline |
| **Beta** | 14–30 Hz | Active thinking, problem solving, acute anxiety/stress |
| **Gamma** | 31–50 Hz | High-level cognition, intense focus, neural binding |

---

### Stage E: Dual-Domain Feature Extraction

#### Differential Entropy (DE) — Frequency Domain

Instead of raw power values, the system computes **Differential Entropy (DE)**, which measures the unpredictability and complexity of a continuous brain signal.

For an EEG signal following a normal distribution within a fixed time window, DE is mathematically equivalent to the natural logarithm of PSD:

$$DE = \frac{1}{2} \ln(P_i) + \frac{1}{2} \ln(2\pi e N) \approx \ln(\text{PSD}) + \text{constant}$$

Where:
- $P_i$ = integrated spectral power within a canonical frequency band
- $N$ = temporal length of the calculation window

The log transform stabilizes volatile power spikes into smooth, linear values that an ML classifier can reliably separate.

#### Hjorth Parameters — Time Domain

Extracted simultaneously within every 20-second window to capture raw speed and structural irregularity of the signal:

| Parameter | Definition |
|-----------|------------|
| **Activity** | Total signal power / variance |
| **Mobility** | Mean frequency factor |
| **Complexity** | Shape deviation from a perfect sine wave |

Combining DE (frequency domain) and Hjorth parameters (time domain) provides a multi-dimensional view of neural stability.

#### One-Way ANOVA Feature Selection

High-dimensional multi-domain feature vectors are prone to noise. After extraction, a **One-Way ANOVA filter** tests whether each feature shows statistically significant variance across calibration target states:

- Features failing to meet the significance threshold (**p > 0.05**) are **discarded**.
- Only statistically relevant, biologically meaningful features pass to the classification layer.

---

### Stage F: Spatial Concatenation & Scaling

#### Building the Feature Vector

With 30 active EEG channels (electrodes), each contributing 5 DE values (one per brainwave band), the system concatenates all values into a single flat row:

$$\text{Vector} = \left[ \underbrace{Ch1_\delta, Ch1_\theta, Ch1_\alpha, Ch1_\beta, Ch1_\gamma}_{\text{Channel 1}}, \underbrace{Ch2_\delta, \ldots}_{\text{Channel 2}}, \ldots, \underbrace{Ch30_\gamma}_{\text{Channel 30}} \right]$$

**Final feature vector length: 30 × 5 = 150 values**

#### Z-Score Normalization

People have varying skull thicknesses and baseline signal strengths. To prevent any single electrode from dominating the model, **Z-score normalization** is applied to the full feature vector:

- Collective mean → **0**
- Standard deviation → **1**

---

## Real-Time Windowing Matrix

The system uses a **continuous sliding time-window framework** to track mental states without processing lag:

```
Time-Series Data Stream:
┌─────────────────────────────────────┐
│          20 Seconds Window          │
└─────────────────────────────────────┘
    |← 2s →| (Stride Shift)
        ┌─────────────────────────────────────┐
        │          20 Seconds Window          │
        └─────────────────────────────────────┘
            |← 2s →| (Stride Shift)
                ┌─────────────────────────────────────┐
                │          20 Seconds Window          │
                └─────────────────────────────────────┘
```

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Window Width** | 20 seconds | Long enough to capture slow Delta/Theta variations while keeping signal structure stable |
| **Stride / Latency** | 2 seconds | Dashboard updates 30×/minute — near real-time responsiveness |

---

## Neurobiological Classification Profiles

### 3.1 Major Depressive Disorder (MDD)

- **Neural Focus:** Frontal and prefrontal cortex (electrodes `Fp1`, `Fp2`, `Fpz`)
- **Spectral Marker:** Changes in Alpha and Beta power; significant left-right hemispheric asymmetry
- **Key Indicator:** Altered frontal alpha activity and hemispheric asymmetry have been repeatedly reported in depression-related EEG studies.

### 3.2 Anxiety Disorders

- **Neural Focus:** Prefrontal cortex + occipital cortex (back of head) during active stress episodes
- **Spectral Marker:** Elevated Theta/Beta ratio; higher Beta and Gamma power (14–50 Hz) in frontal regions
- **Hjorth Signature:** Active panic and overthinking states display a concurrent spike in **frontal Hjorth Mobility** alongside elevated Beta/Gamma DE values

### 3.3 Epileptic Seizure Activity

- **Neural Focus:** Rapid, widespread spikes altering signal size and shape across the full scalp
- **Spectral Marker:** Sudden, intense surges in low-frequency Delta and Theta bands during a seizure event
- **Hjorth Signature:** The "drop in signal complexity" is quantified by a massive, sudden decline in **Hjorth Complexity** alongside a dramatic surge in **Hjorth Activity**

---

## Functional Connectivity Analysis

Traditional EEG analysis isolated electrode behaviors. However, conditions like depression and anxiety involve large-scale brain communication network disruptions. The data processing layer therefore runs a concurrent network-mapping pipeline alongside the main feature log extraction pipeline.

### Step A: Multi-Channel Signal Ingestion

Within the 20-second sliding data window ($\mathcal{W}$), extract the processed time-series voltage array for all channels. For a 30-channel array ($N=30$), let $x_i[n]$ represent the filtered time-series data points from channel $i$, and $x_j[n]$ represent channel $j$.

### Step B: Bandpass Extraction

Isolate the specific canonical frequency band to investigate (e.g., the Alpha band $8\text{–}13\text{ Hz}$ for Major Depressive Disorder, or Beta $14\text{–}30\text{ Hz}$ for Anxiety) using a 10th-order Butterworth filter.

### Step C: Analytical Signal Transformation via Hilbert Transform

To compute phase relationships, calculate the analytical representation $z(t)$ of the bandpassed time-series signal for every channel:

$$z(t) = x(t) + iH\{x(t)\} = A(t)e^{i\phi(t)}$$

Where $H\{x(t)\}$ is the Hilbert Transform of the signal, $A(t)$ is the instantaneous amplitude, and $\phi(t)$ is the instantaneous phase value at each millisecond timestamp.

### Step D: Phase Lag Index (PLI) Matrix Construction

To minimize "volume conduction effects"—where a single deep-brain electrical burst spreads through the skull and creates a false illusion of synchronized regional communication—the Phase Lag Index (PLI) is calculated. PLI ignores zero and $\pi$ phase lags, isolating only true, delayed, non-zero phase communication between electrode pairs.

For every electrode pair $i$ and $j$ across the 30 channels, calculate the PLI value across all sampling points $K$ within the window:

$$\text{PLI}_{ij} = \left| \frac{1}{K} \sum_{k=1}^{K} \text{sign}\left( \Delta\phi_{ij}(t_k) \right) \right|$$

Where $\Delta\phi_{ij}(t_k) = \phi_i(t_k) - \phi_j(t_k)$ is the phase difference between channel $i$ and channel $j$ at time step $k$.

The sign function returns $+1$ if the phase difference is positive, and $-1$ if negative. If two channels are randomly coupled, the average sign yields $0$. If their phase relationship is consistently coupled with a structural time lag, the value approaches $1$.

### Step E: Cross-Channel Connectivity Matrix Creation

This loop outputs a symmetrical $30 \times 30$ connectivity tracking matrix for each frequency band:

$$\mathbf{M}_{\text{PLI}} = \begin{bmatrix}
1.0 & \text{PLI}_{1,2} & \dots & \text{PLI}_{1,30} \\
\text{PLI}_{2,1} & 1.0 & \dots & \text{PLI}_{2,30} \\
\vdots & \vdots & \ddots & \vdots \\
\text{PLI}_{30,1} & \text{PLI}_{30,2} & \dots & 1.0
\end{bmatrix}$$

---

## Personalized EEG Baseline Framework

Neural patterns are highly subjective; a pattern indicating high stress or cognitive impairment in one person may be a baseline physiological state in another. Nurolab uses a multi-state baseline calibration block to build an individual reference index.

```text
┌──────────────────────────────────────────────────────────┐
│ Phase 1: 4-Part Calibration App Routine (Ground Truth)    │
└───────────────────────────┬──────────────────────────────┘
                             │
   ┌───────────────┬─────────────────┬─────────────────┬─────────────────┐
   ▼               ▼                 ▼                 ▼
┌───────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Resting   │  │ Focus Task   │  │ Relaxation   │  │ Emotional        │
│ State     │  │              │  │ Task         │  │ Stimuli Task     │
└─────┬─────┘  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
      │               │                 │                   │
      └───────────────┴─────────────────┴───────────────────┘
                             │
                             ▼
       ┌────────────────────────────────────────────────────────┐
       │ Dynamic Feature Array Collection & Statistics Mapping   │
       └───────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Individual Reference Index Matrix (Mean, Median, SD)    │
       └────────────────────────────────────────────────────────┘
```

### The Calibration App Routine

Before active system monitoring begins, the user runs through a 4-part calibration app routine to record ground-truth metrics:

- **Resting State**: User sits quietly with eyes closed (captures peak Alpha baseline).
- **Focus Task**: User performs an active cognitive/attention task (captures high-load Beta/Gamma baseline).
- **Relaxation Task**: User engages in a guided relaxation exercise (captures low-arousal baseline).
- **Emotional Stimuli Task**: User views a verified emotionally resonant audio-video clip (captures baseline emotional thresholds).

### Mathematical Baseline Processing Workflow

During these calibration states, the system bypasses classification and routes the incoming 20-second sliding windows into a raw statistics mapping array:

- Collect the 150-dimensional feature vector (containing Differential Entropy values across 5 bands for 30 channels) every 2 seconds.
- Calculate time-domain Hjorth parameters (Activity, Mobility, Complexity).
- Flatten the $30 \times 30$ PLI connectivity matrix into a one-dimensional array.

### Individual Reference Index Generation

The system accumulates these values across all calibration tasks and computes the historical **Mean ($\mu$)**, **Median ($\tilde{x}$)**, and **Standard Deviation ($\sigma$)** for every individual biomarker parameter, across the following feature groups:

- Differential Entropy (per band, per channel)
- Hjorth Parameters (Activity, Mobility, Complexity)
- Connectivity Metrics (PLI / connectivity matrices)
- Frequency Band Powers

This creates a static personal baseline dictionary used to normalize all future real-time tracking runs:

```text
Ref_User = {
  DE_Fp1_beta            : [μ = 1.24, σ = 0.12],
  Hjorth_Fz_Mobility     : [μ = 0.45, σ = 0.03],
  PLI_F3_F4_alpha        : [μ = 0.32, σ = 0.04]
}
```
---

## Deviation Detection Engine

Instead of evaluating single, static EEG segments out of context, Nurolab uses an ongoing anomaly and drift-monitoring workflow. It evaluates whether current real-time neural activity significantly drifts away from the individual user's historical calibrations.

### Real-Time Algorithmic Sequence

```text
Feature Extraction
↓
Baseline Profile
↓
Mahalanobis Distance
↓
CUSUM Detection
↓
Trigger Event
```

### Step 1: Real-Time Vector Computation

During live tracking, compute the user's active brainwave features ($\mathbf{X}_{\text{current}}$) every 2 seconds across the sliding window. This captures:

- Logarithmic Differential Entropy ($\text{DE}$) values.
- Time-domain parameters (Hjorth Activity, Mobility, Complexity).
- Active Functional Connectivity network maps (PLI).

### Step 2: Distance Metrics Computation

To capture multi-channel parameter changes simultaneously without treating features as isolated variables, calculate the statistical distance between the current active window vector ($\mathbf{X}_{\text{current}}$) and the saved calibration baseline cluster ($\mathbf{\mu}_{\text{baseline}}$).

Compute the Mahalanobis Distance ($D_M$) to account for correlations between multi-electrode neural features:

$$D_M(\mathbf{X}_{\text{current}}) = \sqrt{(\mathbf{X}_{\text{current}} - \mathbf{\mu}_{\text{baseline}})^T \mathbf{\Sigma}^{-1} (\mathbf{X}_{\text{current}} - \mathbf{\mu}_{\text{baseline}})}$$

Where $\mathbf{\Sigma}^{-1}$ is the inverse covariance matrix calculated during the initial personalized baseline phase.

### Step 3: Statistical Deviation Scoring

For quick, single-electrode tracking variables (such as checking for an acute prefrontal overthinking spike), compute a real-time running Z-Score deviation value against the saved personalized baseline profile:

$$Z_{\text{feature}} = \frac{X_{\text{current}} - \mu_{\text{baseline}}}{\sigma_{\text{baseline}}}$$

### Step 4: CUSUM Change-Point Detection

To detect sustained, gradual drifts in a feature's distribution over time (rather than momentary spikes), apply a Cumulative Sum (CUSUM) change-point detection procedure on top of the Z-scored feature stream. This flags persistent shifts away from baseline that single-window Z-scores or Mahalanobis distances alone may miss.

### Step 5: Closed-Loop Intervention Logic Threshold Check

The platform monitors for specific target condition deviations based on clinical research-supported feature directions:

**Anxiety / Overthinking Deviation Trigger:**

$$\text{IF } \left( Z_{\text{DE}(\text{Prefrontal }\beta\gamma)} > +2.5 \right) \quad \mathbf{AND} \quad \left( Z_{\text{Hjorth-Mobility}(\text{Frontal})} > +2.0 \right)$$

*Neurobiological Meaning*: Prefrontal high-frequency processing complexity and signal speed have surged significantly above the individual's baseline calibration range. This flags a possible active rumination loop or panic spike.

**Depressive State Deviation Trigger:**

$$\text{IF } \left( \text{Mean}(Z_{\text{Alpha-Asymmetry}}) \text{ shifts continuously for } > 5 \text{ minutes} \right) \quad \mathbf{AND} \quad \left( \text{Significant deviations from the individual's baseline connectivity profile (}\mathbf{M}_{\text{PLI}(\alpha\beta)}\text{)} \right)$$

*Neurobiological Meaning*: Frontal alpha asymmetry has drifted significantly from baseline, accompanied by a meaningful change in global network communication efficiency relative to the user's own calibrated profile. This may indicate a transition into a deeper depressive state rather than a momentary mood fluctuation.

> **Note:** The literature does not support a universal fixed threshold (e.g., a flat percentage drop) for connectivity changes across individuals. Deviation triggers are therefore expressed relative to the individual's personalized baseline distribution rather than as an absolute clinical cutoff.

**Epileptic Seizure Anomaly Trigger:**

$$\text{IF } \left( Z_{\text{Hjorth-Activity}} > +4.0 \right) \quad \mathbf{AND} \quad \left( Z_{\text{Hjorth-Complexity}} \to -3.5 \right)$$

*Neurobiological Meaning*: The signal displays a massive, sudden surge in raw wave volume paired with a sharp drop in geometric irregularity. This indicates hyper-synchronous neural firing across the network topology.

### Step 6: Execute Micro-Journaling Intervention

If any trigger condition resolves to TRUE, the application dashboard captures the exact timestamp of the neural deviation breach and immediately displays the closed-loop micro-journaling input panel overlay: a prompt asking the user to note what was on their mind at that moment. This links objective physiological data directly with real-time cognitive context.

---

## Risk Indicator Framework

### Feature Fusion & Machine Learning Layer

```text
Frequency Features (PSD, DE)
+
Time Features (Hjorth)
+
Connectivity Features (PLV, PLI, Coherence)
+
Deviation Features
↓
Feature Fusion Layer
↓
ANOVA Feature Selection
↓
SVM / XGBoost
↓
Risk Score
```

This extends the original SVM-only classification stage by combining frequency-domain, time-domain, connectivity, and deviation-derived features into a single fusion layer before feature selection and classification. SVM remains well-validated for EEG classification tasks, while XGBoost is widely used for tabular biomedical feature sets and is a realistic, interpretable next step before considering deep architectures such as CNN/LSTM.

### Risk Tiering

Rather than outputting discrete diagnostic labels (e.g., "Depressed" / "Anxious"), the system outputs a tiered risk indicator:

- **Low Risk**
- **Moderate Risk**
- **High Risk**

This framing is more clinically responsible, better aligned with research-stage claims, and easier to justify to institutional reviewers, since it avoids implying a diagnostic determination.

---

## Trigger Detection & Closed-Loop Therapy

A key differentiator of this system is identifying the **initial cognitive trigger** — the precise moment a single negative thought or stressor starts a downward emotional trend.

```
┌──────────────────┐     Real-Time Stream     ┌───────────────────────────────┐
│  Patient Scalp   │ ────────────────────────► │  20s Window / 2s Stride DE   │
│  EEG Electrodes  │                           │  Processing Architecture      │
└──────────────────┘                           └───────────────┬───────────────┘
         ▲                                                     │
         │  Real-Time Feedback Loop                            ▼
         │  Threshold Breach Alert               ┌─────────────────────────────┐
┌────────┴──────────┐                            │  PFC Beta/Gamma Power Spike │
│  Micro-Journaling │ ◄──────────────────────── │  Detection Engine           │
│  Activation Panel │                            └─────────────────────────────┘
└───────────────────┘
```

### Detection Steps

1. **Continuous Baseline Tracking** — Monitors the user's typical Beta/Gamma power levels in the prefrontal cortex during a relaxed state.

2. **Spike Detection** — A sudden surge in prefrontal Beta/Gamma power that breaks through baseline thresholds flags an active overthinking or distress episode.

3. **Immediate Notification** — The application logs the exact timestamp of the spike and surfaces a micro-journaling prompt:
   > *"We noticed a sharp shift in your focus markers just now. What thought was on your mind?"*

4. **Data Correlation** — Links objective biological data directly with the user's self-reported thoughts, helping clinicians map the precise triggers that lead to anxious or depressive states.

---

## Experimental Paradigms

### Phase 1: Calibration Run (Ground Truth Labeling)

**Objective:** Collect clean, labeled data to build an individualized classification profile.

```
┌────────────────────────┐     ┌─────────────────────────────┐     ┌──────────────────────────┐
│  5s Instructional Cue  │────►│  30s Emotional Stimulus     │────►│  Real-Time Labeling      │
│  (Prepare Focus State) │     │  (Video / Audio Clip)       │     │  (Baseline Generation)   │
└────────────────────────┘     └─────────────────────────────┘     └──────────────────────────┘
```

- Each trial: **5-second instructional cue** → **30 seconds of targeted emotional stimuli** (validated video/audio clips)
- Raw EEG data is logged and mapped directly to the corresponding target mental state label

### Phase 2: Closed-Loop Regulation Run (Core Product Experience)

**Objective:** Guide the user through real-time focus and relaxation exercises.

```
┌──────────────────────────┐     ┌──────────────────────────┐     ┌──────────────────────────┐
│  60s Fixation Cross      │────►│  Sliding Window Feature  │────►│  Dynamic Visual Output   │
│  (Internal Regulation)   │     │  (Deep Entropy Vector)   │     │  (Real-Time Reward Bar)  │
└──────────────────────────┘     └──────────────────────────┘     └──────────────────────────┘
```

- User focuses on a fixation cross `(+)` for **60 seconds** while practicing mindfulness or deep breathing
- System processes the 20-second sliding window, extracts the DE feature vector, runs the classifier, and updates a visual progress bar every **2 seconds**
- Immediate feedback trains users to actively regulate their own brain patterns

---

## Classification Modeling

### Core Classifier

The system uses a **multi-class Support Vector Machine (SVM) with a Linear Kernel**, paired with a **One-Versus-One (OVO)** classification strategy — reliable decision boundaries at low computational cost, enabling local real-time inference.

### Multiclass SVM Voting Architecture

```
                    ┌──────────────────────────┐
                    │  Normalized DE Feature   │
                    │        Vector            │
                    └────────────┬─────────────┘
                                 │ Classification Stage
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
  │  SVM Classifier 1 │ │  SVM Classifier 2 │ │  SVM Classifier 3 │
  │ Depression vs.    │ │ Anxiety vs.       │ │ Depression vs.    │
  │ Anxiety           │ │ Epilepsy          │ │ Epilepsy          │
  └─────────┬─────────┘ └────────┬──────────┘ └────────┬──────────┘
            │                    │ Collection Stage      │
            └────────────────────┼───────────────────────┘
                                 ▼
                    ┌────────────────────────────┐
                    │     Integrated Voting      │
                    │     Matrix (Aggregated     │
                    │     Votes for Decision)    │
                    └────────────┬───────────────┘
                                 ▼
                    ┌────────────────────────────┐
                    │   Final Output Label:      │
                    │ Depression / Anxiety /     │
                    │      Epilepsy              │
                    └────────────────────────────┘
```

### Model Controls

| Control | Description |
|---------|-------------|
| **Voting Matrix** | OVO trains one binary classifier per condition pair. Each sub-model casts a vote; the state with the most votes is the final label. |
| **UI Calibration** | During the calibration run, the system computes decision values $w^T x + b$ from each SVM hyperplane. The **median** and **95th percentile** of these values define stable UI tiers, so the interface transitions smoothly based on how deeply established the current mental state is. |

---

## References

1. [Neurofeedback Training With an Electroencephalogram-Based Brain-Computer Interface Enhances Emotion Regulation](https://ieeexplore.ieee.org/iel7/5165369/10138707/09647919.pdf)

2. [Optimal Feature Selection and Deep Learning Ensembles Method for Emotion Recognition From Human Brain EEG Sensors](https://ieeexplore.ieee.org/document/7997991)

3. [EEG Machine Learning with Higuchi Fractal Dimension and Sample Entropy as Features for Successful Detection of Depression](https://arxiv.org/abs/1803.05985)

4. [Alterations in EEG Functional Connectivity in Individuals with Depression: A Systematic Review](https://www.sciencedirect.com/science/article/abs/pii/S0165032723001465)

5. [EEG machine learning with Higuchi fractal dimension and Sample Entropy as features for successful detection of depression](https://arxiv.org/abs/1803.05985)

6. [Role of Machine Learning and Deep Learning Techniques in EEG-Based BCI Emotion Recognition System: A Review](https://link.springer.com/article/10.1007/s10462-023-10690-2?utm_source=chatgpt.com)

7. [EEG-Based Emotion Recognition Using Graph Neural Networks](https://arxiv.org/abs/1907.07835)

8. [Investigating EEG-Based Functional Connectivity Patterns for Emotion Recognition](https://arxiv.org/abs/2004.01973)

9. [A Comprehensive Survey on EEG-Based Emotion Recognition: A Graph-Based Perspective](https://arxiv.org/abs/2408.06027)

10. [4D Attention-Based Neural Network for EEG Emotion Recognition](https://arxiv.org/abs/2101.05484)
