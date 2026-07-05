# Cereqon Android — API Reference

## Backend REST (unchanged)

Aligned with `nurolab/app_backend/server.py`. Client: `BackendApiService` (Retrofit).

| Endpoint | Method | Retrofit | Domain result |
|----------|--------|----------|---------------|
| `/health` | GET | `getHealth()` | `HealthStatus` via `HealthMapper` |
| `/calibration/status` | GET | `getCalibrationStatus()` | `CalibrationStatus` via `CalibrationStatusMapper` |
| `/calibration/build_baseline` | POST | `buildBaseline(relaxedWindows)` | `BaselineResult` via `BaselineResultMapper` |

### Request / response shapes

**`GET /health`**
```json
{ "status": "ok", "version": "1.0.0" }
```

**`GET /calibration/status`**
```json
{
  "calibrated": true,
  "n_features": 128,
  "data_source": "...",
  "models_loaded": ["..."]
}
```

**`POST /calibration/build_baseline`**
- Body: `{ "relaxed_windows": [[float, ...], ...] }` — relaxed feature windows from calibration.
- Response: `{ "status": "baseline_ready", "n_windows": 42 }`

All REST calls use dynamic base URL from `ServerUrlStore` (synced with DataStore).

## WebSocket live stream

| Property | Value |
|----------|-------|
| Path | `/ws/live` |
| Protocol | OkHttp WebSocket (server-push JSON only) |
| Manager | `LiveStreamWebSocketManager` |
| Facade | `LiveStreamRepository` |

### Payload shape (`LivePayloadDto`)

```json
{
  "window_start_time": 0.0,
  "window_end_time": 1.0,
  "feature_vector": [0.1, 0.2],
  "predictions": {
    "condition_name": { "label": "...", "confidence": 0.9 }
  },
  "deviation": {
    "mahalanobis": 1.5,
    "risk_tier": 0,
    "explanations": ["..."]
  }
}
```

Mapped to domain `LiveWindow` by `LivePayloadMapper`.

### Stream connection states (`StreamConnectionState`)

| State | Meaning |
|-------|---------|
| `DISCONNECTED` | Not connected |
| `CONNECTING` | WebSocket opening |
| `WARMUP` | Connected, awaiting first payload (~20 s) |
| `STREAMING` | Receiving windows |
| `RECONNECTING` | Backoff reconnect in progress |
| `FAILED` | Unrecoverable connection failure |

## Repository interfaces

### `HealthRepository`

```kotlin
suspend fun checkHealth(): Outcome<HealthStatus>
suspend fun getCachedHealth(): HealthStatus?
```

### `CalibrationRepository`

```kotlin
suspend fun getStatus(): Outcome<CalibrationStatus>
suspend fun submitBaseline(relaxedWindows: List<List<Float>>): Outcome<BaselineResult>
```

### `LiveStreamRepository`

```kotlin
val connectionState: StateFlow<StreamConnectionState>
val reconnectAttemptCount: StateFlow<Int>
val windows: Flow<LiveWindow>
fun start()
fun stop()
```

### `SettingsRepository`

```kotlin
val serverBaseUrl: Flow<String>
val onboardingCompleted: Flow<Boolean>
val lastKnownCalibrated: Flow<Boolean>
suspend fun setServerBaseUrl(url: String)
suspend fun setOnboardingCompleted(completed: Boolean)
suspend fun setLastKnownCalibrated(calibrated: Boolean)
suspend fun getServerBaseUrl(): String
```

### `InsightsRepository` (Phase 5A)

```kotlin
suspend fun getActiveSession(): InsightSession?
suspend fun getSession(sessionId: Long): InsightSession?
suspend fun getWindowSnapshots(sessionId: Long): List<InsightWindowSnapshot>
suspend fun countWindowSnapshots(sessionId: Long): Int
suspend fun startSession(serverBaseUrl: String, calibratedAtStart: Boolean): Long
suspend fun endSession(sessionId: Long, endedAtEpochMs: Long)
suspend fun recordWindowSnapshot(sessionId: Long, window: LiveWindow): Long
```

Read-through and write-through to Room only. No analytics or derived metrics.

## Domain models

| Model | Source | Notes |
|-------|--------|-------|
| `HealthStatus` | REST | `status`, `version` |
| `CalibrationStatus` | REST | Calibration readiness |
| `BaselineResult` | REST | Baseline build outcome |
| `LiveWindow` | WebSocket | Full live window with features, predictions, deviation |
| `FeatureVector` | WebSocket | Named feature values |
| `Prediction` | WebSocket | Sealed: `Success` / `Failed` |
| `DeviationSnapshot` | WebSocket | Mahalanobis, risk tier, explanations |
| `RiskTier` | WebSocket | Enum `BASELINE(0)` … `SIGNIFICANT(3)` |
| `BrainMetrics` | Client-computable | Not exposed over WebSocket; unused in current features |
| `Outcome<T>` | App | `Success`, `Error`, `Loading` |
| `InsightSession` | Room | Persisted session metadata |
| `InsightWindowSnapshot` | Room | Persisted window summary per session |

## Room schema (`cereqon.db` v1)

| Table | Entity | DAO | Wired to repository |
|-------|--------|-----|---------------------|
| `sessions` | `SessionEntity` | `SessionDao` | `InsightsRepository` |
| `window_snapshots` | `WindowSnapshotEntity` | `WindowSnapshotDao` | `InsightsRepository` |
| `calibration_attempts` | `CalibrationAttemptEntity` | `CalibrationAttemptDao` | Not wired |
| `reports` | `ReportEntity` | `ReportDao` | Not wired |

### `WindowSnapshotEntity` fields

| Column | Type | Populated from `LiveWindow` |
|--------|------|----------------------------|
| `session_id` | Long | Caller |
| `window_start_time` | Double | `windowStartTime` |
| `window_end_time` | Double | `windowEndTime` |
| `captured_at_epoch_ms` | Long | `receivedAtEpochMs` |
| `risk_tier` | Int? | `deviation?.riskTier?.value` |
| `mahalanobis` | Double? | `deviation?.mahalanobis` |
| `predictions_json` | String? | `null` (deferred) |

## DataStore keys (`cereqon_settings`)

| Key | Type | Purpose |
|-----|------|---------|
| `server_base_url` | String | Backend base URL |
| `onboarding_completed` | Boolean | Welcome flow completed |
| `last_known_calibrated` | Boolean | Last known calibration state |
