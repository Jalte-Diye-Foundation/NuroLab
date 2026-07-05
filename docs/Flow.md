# Cereqon Android — Application Flow

## Onboarding flow (current)

```
Welcome ──health OK──▶ Calibration ──baseline OK──▶ Dashboard
                                                      │
                                                      └── Settings (gear only; Insights/Reports not linked from UI)
```

Navigation uses `popUpTo { inclusive = true }` so the user cannot navigate back to completed onboarding steps.

| Step | Route | Trigger | Outcome |
|------|-------|---------|---------|
| 1 | `welcome` | App launch (`startDestination`) | User enters server URL, tests `GET /health` |
| 2 | `calibration` | Continue after successful health check | 5-minute live stream collection → `POST /calibration/build_baseline` |
| 3 | `dashboard` | Baseline upload success | Live WebSocket dashboard; persists windows to Room |
| 4 | `insights` | *(not reachable from UI)* | Route registered; `InsightsNavigationEntry` has no screen composables |
| 5 | `reports` | *(not reachable from UI)* | Route registered; list UI only, no export actions wired |

**Note:** `startDestination` is always `Routes.WELCOME`. Onboarding-completion routing (skip Welcome when already set up) is not yet implemented.

## Welcome flow

```mermaid
sequenceDiagram
    participant UI as WelcomeScreen
    participant VM as WelcomeViewModel
    participant Settings as SettingsRepository
    participant Health as HealthRepository
    participant API as BackendApiService

    UI->>VM: onServerUrlChanged(url)
    UI->>VM: testConnection()
    VM->>Settings: setServerBaseUrl(url)
    VM->>Health: checkHealth()
    Health->>API: GET /health
    API-->>Health: HealthResponseDto
    Health-->>VM: Outcome.Success(HealthStatus)
    VM-->>UI: LoadableUiState.Success
    UI->>VM: onContinue()
    VM->>Settings: setOnboardingCompleted(true)
    UI->>Nav: navigate(CALIBRATION)
```

## Calibration flow

```mermaid
sequenceDiagram
    participant UI as CalibrationScreen
    participant VM as CalibrationViewModel
    participant Stream as LiveStreamRepository
    participant Cal as CalibrationRepository
    participant Insights as InsightsRepository

    UI->>VM: startCalibration()
    VM->>Stream: start()
    Stream-->>VM: connectionState (CONNECTING → WARMUP → STREAMING)
    Stream-->>VM: windows (LiveWindow)
    Note over VM: 300s countdown, collect feature vectors
    VM->>Insights: recordWindowSnapshot (per window)
    VM->>Stream: stop()
    VM->>Insights: endSession
    VM->>Cal: submitBaseline(vectors)
    Cal-->>VM: Outcome.Success(BaselineResult)
    VM-->>UI: CalibrationEvent.NavigateToDashboard
```

**Stream states during calibration:** `CONNECTING` → `WARMUP` (~20 s server warmup) → `STREAMING` → collection → `stop()`.

## Dashboard flow

```mermaid
sequenceDiagram
    participant UI as DashboardScreen
    participant VM as DashboardViewModel
    participant Stream as LiveStreamRepository
    participant Settings as SettingsRepository
    participant Insights as InsightsRepository
    participant Room as SessionDao / WindowSnapshotDao

    VM->>Stream: start() [init]
    VM->>Settings: getServerBaseUrl()
    VM->>Insights: startSession()
    Stream-->>VM: connectionState (StateFlow)
    Stream-->>VM: reconnectAttemptCount (StateFlow)
    Stream-->>VM: windows (Flow)
    VM->>Insights: recordWindowSnapshot (per window)
    Insights->>Room: insert snapshot
    Note over VM: Append to DashboardTimelineHistory (max 60)
    Note over VM: 1s ticker for packet age
    UI->>VM: refresh() [pull-to-refresh]
    VM->>Stream: stop() → start()
    VM->>Insights: endSession [onCleared]
```

Dashboard **owns** the WebSocket stream and **writes** window snapshots to Room. Chart timeline (`DashboardTimelineHistory`) remains in-memory only.

## Insights flow (Phase 5A — architecture only)

```mermaid
sequenceDiagram
    participant Nav as InsightsNavigationEntry
    participant VM as InsightsViewModel
    participant Insights as InsightsRepository
    participant Stream as LiveStreamRepository
    participant Room as SessionDao / WindowSnapshotDao

    Nav->>VM: hiltViewModel() [lifecycle retained, no UI]
    VM->>Stream: connectionState.collect (read-only)
    VM->>Insights: observeActiveSession()
    Insights->>Room: observeActiveSession() Flow
    VM->>Insights: observeWindowSnapshots(sessionId)
    Insights->>Room: observeBySession() Flow
    Note over Room: Dashboard writes trigger re-emission
    VM-->>Nav: InsightsUiState (StateFlow)
```

**Insights route:** `Routes.INSIGHTS` is registered in `CereqonNavHost` but **Dashboard has no button** that calls `onNavigateToInsights` (callback exists, parameter is unused). No visual composables on the Insights screen yet.

**Read path:** reactive Room `Flow` — no one-shot cache loads.  
**Write path:** owned by Dashboard and Calibration; Insights never writes.

## Live stream connection lifecycle

```
DISCONNECTED
    │ start()  [Dashboard or Calibration only]
    ▼
CONNECTING ──WebSocket open──▶ WARMUP ──first payload──▶ STREAMING
    │                              │                        │
    │                              │                        │ connection lost
    │                              │                        ▼
    │                              │                   RECONNECTING
    │                              │                   (exponential backoff)
    │                              │                        │
    │                              └─────── failed ────────▶ FAILED
    │
    └── stop() ──▶ DISCONNECTED
```

Managed by `LiveStreamWebSocketManager` (singleton, `@ApplicationScope`).

### Stream ownership summary

| Caller | `start()` | `stop()` | `windows.collect` | `connectionState` observe |
|--------|-----------|----------|---------------------|---------------------------|
| DashboardViewModel | Yes | Yes (`onCleared`) | Yes | Yes |
| CalibrationViewModel | Yes | Yes | Yes | Yes |
| InsightsViewModel | **No** | **No** | **No** | Yes (offline semantics) |

## Offline / cache semantics (Insights)

| Stream state | Cached Room data | `OfflineUiState` |
|--------------|------------------|------------------|
| STREAMING, WARMUP, CONNECTING, RECONNECTING | any | `Online` |
| DISCONNECTED, FAILED | session or snapshots exist | `OfflineWithCache(lastCachedAtEpochMs)` |
| DISCONNECTED, FAILED | none | `OfflineNoCache` |

Room observers keep `InsightsUiState` current while Dashboard writes snapshots; no manual refresh required.
