# NuroLab — Architecture & Status

Last updated: today, reflects everything built and tested so far.


## 1. What's LIVE right now (in the real-time /ws/live stream)

Every ~2 seconds, connected clients receive:

- `alpha_de, beta_de, theta_de, delta_de, gamma_de` — all 5 EEG band powers
- `alpha_beta_ratio, engagement_index, relaxation_index, cognitive_load, signal_quality`
- `deviation_score, risk_tier` — z-score deviation from personal baseline
- `stress_prediction, attention_prediction, fatigue_prediction`
- `data_source` — "simulated" or "live_headset"
- `feature_vector` — full 64-length feature vector (8ch x 8 features), used for the deviation engine
- `epilepsy` — only present when `data_source == "live_headset"`
- `mahalanobis_deviation` — only present when the connected user has a full-feature baseline (see Section 3)


## 2. Backend — all working endpoints

Health check, calibration (build + status), session (save + history),
live WebSocket stream, hardware status + ingestion WebSocket, model
status, clinical model status + predictions (epilepsy/depression), PDF
report generation. Full list and exact paths in `nurolab/README.md`.


## 3. Mahalanobis deviation engine — built, tested, NOT yet default

**Status:** all 4 build stages complete and merged. Proven to catch a
real, specific anomaly (one channel, consistent across 10+ windows) that
the current z-score method structurally can't isolate.

**Why it's not live yet:** tested against a single ~3-minute recording,
covariance rank coverage is only ~20% of the feature space — genuinely
promising, not yet enough calibration data for full production
reliability. Currently runs as an additional field (`mahalanobis_deviation`)
alongside the existing method, not replacing it.

**What would make it production-ready:** either combine multiple real
recordings for a larger calibration set, or formalize the DE-only
feature reduction (320→200 features) as the permanent approach — both
meaningfully improved rank coverage and numerical stability in testing.


## 4. Signal processing pipeline

Raw EEG → blink removal → bandpass (0.1-70Hz) + notch (50Hz) filter,
matching order between training and live → 20s windows, 2s stride →
feature extraction (5 DE bands + 3 Hjorth params per channel).

`fs=250.0` for the live/simulated source (real ADS1299 hardware limit,
not 256).


## 5. ML models

| Model | Accuracy | Status |
|---|---|---|
| Epilepsy | ~89% | Production-usable, still recommend validating on your own data |
| Depression | ~38% (7 subjects) | Experimental only — reliability_warning always present |
| Stress/attention/fatigue | heuristic fallback if no `.pkl` present | Functional |


## 6. Hardware integration

Real headset firmware pushes to `/ws/ingest/headset`. `/ws/live`
automatically prefers real data over simulated once enough real
samples arrive (checked via `/hardware/status`). Physical headset
itself still in procurement — software side fully ready.


## 7. Flutter mobile app

Connect screen, live dashboard (all metrics above), calibration flow,
session history with PDF report download. Built via GitHub Actions
(zero local Flutter install needed). Requires `--host 0.0.0.0` on the
server and matching WiFi network to actually reach the backend from a
phone.


## 8. What's next (not started)

- **Cognitive fatigue trend tracking** — watching `cognitive_load`
  (already computed, = theta/alpha ratio) over the course of a session
  to detect a genuine rising trend, not just a point-in-time value
- Public backend deployment (currently local-only)
- Combining multiple recordings for a production-ready Mahalanobis
  calibration set
- Stress detection (DEAP dataset), ADHD monitoring (PhysioNet) — future
  research direction, not started
