# Cereqon Android — State Management

## Principles

1. **Single source of truth** — ViewModels own UI state via `StateFlow`.
2. **Unidirectional data flow** — UI reads state; events call ViewModel methods.
3. **Repository boundaries** — ViewModels never access DAOs, Retrofit, or WebSocket directly.
4. **Immutable UI state** — `data class` / `sealed interface` copies updated with `.copy()`.

## State exposure pattern

Every feature ViewModel follows:

```kotlin
private val _uiState = MutableStateFlow(FeatureUiState())
val uiState: StateFlow<FeatureUiState> = _uiState.asStateFlow()
```

Screens collect with:

```kotlin
val uiState by viewModel.uiState.collectAsStateWithLifecycle()
```

## Shared state types

### `LoadableUiState<T>`

Used for one-shot or refreshable operations (Welcome health check, Calibration baseline submit, Insights cache load).

| Variant | Meaning |
|---------|---------|
| `Idle` | Not started |
| `Loading` | In progress |
| `Success<T>(data)` | Completed with value |
| `Error(message, retry?)` | Failed; optional retry lambda |

**Used by:** `WelcomeViewModel`, `CalibrationViewModel`, `InsightsViewModel`

### `OfflineUiState`

Used for cache availability when the live stream is unavailable.

| Variant | Meaning |
|---------|---------|
| `Online` | Live stream active or connecting |
| `OfflineNoCache` | Offline, no Room data |
| `OfflineWithCache(lastSyncAtEpochMs)` | Offline, historical data available |

**Used by:** `InsightsViewModel` (designed for Reports in future)

### `Outcome<T>` (domain)

Repository return type for REST operations. Mapped to `LoadableUiState` in ViewModels.

| Variant | Meaning |
|---------|---------|
| `Success(value)` | Operation succeeded |
| `Error(message, cause?)` | Operation failed |
| `Loading` | Reserved (not emitted by current repos) |

## Feature state models

### `WelcomeUiState`

| Field | Type | Source |
|-------|------|--------|
| `serverUrl` | `String` | User input / DataStore |
| `connectionState` | `LoadableUiState<HealthStatus>` | Health check |
| `isSaving` | `Boolean` | Continue action |
| `setupComplete` | `Boolean` | Navigation gate |

Derived: `canContinue` — health check succeeded.

### `CalibrationUiState`

| Field | Type | Source |
|-------|------|--------|
| `phase` | `CalibrationPhase` | State machine |
| `streamConnectionState` | `StreamConnectionState` | Live stream |
| `remainingSeconds` | `Int` | Countdown timer |
| `collectedWindows` | `Int` | Window collector |
| `progressFraction` | `Float` | UI progress bar |
| `submitState` | `LoadableUiState<BaselineResult>` | Baseline upload |
| `errorMessage` | `String?` | Error display |

Derived: `formattedRemainingTime`, `isActive`

**Navigation:** `Channel<CalibrationEvent>` → `NavigateToDashboard` (one-shot event, not in UiState).

### `DashboardUiState`

| Field | Type | Source |
|-------|------|--------|
| `connectionState` | `StreamConnectionState` | Live stream |
| `latestWindow` | `LiveWindow?` | Latest WebSocket window |
| `serverBaseUrl` | `String` | Settings |
| `lastUpdateEpochMs` | `Long?` | Latest window timestamp |
| `secondsSinceLastPacket` | `Long?` | 1 s ticker |
| `reconnectAttemptCount` | `Int` | WebSocket manager |
| `isRefreshing` | `Boolean` | Pull-to-refresh |
| `errorMessage` | `String?` | Connection failure |
| `history` | `DashboardTimelineHistory` | In-memory chart buffer (max 60) |

Derived: `connectionQuality`, `isAutoReconnecting`, `isLoading`, `isStreaming`, `hasPayload`, etc.

**Pattern:** Flat `data class` with computed vals — no `LoadableUiState` wrapper for the live stream.

### `InsightsUiState` (Phase 5A)

| Field | Type | Source |
|-------|------|--------|
| `connectionState` | `StreamConnectionState` | `LiveStreamRepository` (observe only) |
| `serverBaseUrl` | `String` | Settings |
| `offlineState` | `OfflineUiState` | Derived from connection + cache |
| `sessionState` | `LoadableUiState<InsightSession?>` | Room via `InsightsRepository` |
| `snapshotsState` | `LoadableUiState<List<InsightWindowSnapshot>>` | Room via `InsightsRepository` |
| `snapshotCount` | `Int` | Room count query |

Derived: `isStreaming`, `hasActiveSession`, `hasCachedSnapshots`, `lastCachedAtEpochMs`

**No UI yet** — state is collected in `InsightsNavigationEntry` for pipeline validation.

## Collector patterns

### Reactive stream collection (Dashboard, Calibration, Insights)

```kotlin
viewModelScope.launch {
    liveStreamRepository.connectionState.collect { state ->
        _uiState.update { it.copy(connectionState = state) }
    }
}
```

### One-shot load (Welcome, Insights refresh)

```kotlin
viewModelScope.launch {
    _uiState.update { it.copy(sessionState = LoadableUiState.Loading) }
    val session = insightsRepository.getActiveSession()
    _uiState.update { it.copy(sessionState = LoadableUiState.Success(session)) }
}
```

### Timer loop (Dashboard packet age)

```kotlin
viewModelScope.launch {
    while (isActive) {
        delay(1_000)
        _uiState.update { /* recompute secondsSinceLastPacket */ }
    }
}
```

## Lifecycle

| ViewModel | `onCleared()` behavior |
|-----------|------------------------|
| `DashboardViewModel` | `liveStreamRepository.stop()` |
| `CalibrationViewModel` | Cancel countdown; `liveStreamRepository.stop()` |
| `InsightsViewModel` | No stream control (observe only) |
| `WelcomeViewModel` | No cleanup |

## In-memory vs persisted state

| Data | Storage | Scope |
|------|---------|-------|
| Latest live window | ViewModel `DashboardUiState` | Process |
| Chart timeline (60 pts) | `DashboardTimelineHistory` | Process |
| Session / snapshots | Room | Disk |
| Server URL, flags | DataStore | Disk |
| Health cache | `HealthRepositoryImpl` volatile field | Process |

## State management anti-patterns (avoided)

- No `LiveData` — Coroutines `StateFlow` throughout.
- No direct DAO access from ViewModels.
- No analytics computation in UiState derived properties (Dashboard `connectionQuality` is transport health only).
- No fake/sample data in production state paths.
