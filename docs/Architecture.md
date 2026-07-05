# Cereqon Android — Architecture

**Package:** `org.jaltediye.cereqon`  
**Pattern:** Clean Architecture with MVVM presentation layer  
**DI:** Dagger Hilt (`@HiltAndroidApp`, `@HiltViewModel`, `@Singleton`)

## Layer overview

```
┌─────────────────────────────────────────────────────────────┐
│  presentation/   Compose screens, ViewModels, UI state      │
├─────────────────────────────────────────────────────────────┤
│  domain/         Models, repository interfaces (no Android)  │
├─────────────────────────────────────────────────────────────┤
│  data/           Repository impls, Room, Retrofit, WebSocket │
├─────────────────────────────────────────────────────────────┤
│  di/             Hilt modules (network, database, repos)    │
└─────────────────────────────────────────────────────────────┘
```

Dependency rule: **presentation → domain ← data**. Domain has no Android or framework imports.

## Modules

| Module | Location | Responsibility |
|--------|----------|----------------|
| **Presentation** | `presentation/` | Jetpack Compose UI, `@HiltViewModel`, `StateFlow` UI state |
| **Domain** | `domain/model/`, `domain/repository/` | Business models, repository contracts |
| **Data** | `data/` | REST, WebSocket, Room, DataStore, mappers |
| **DI** | `di/` | Hilt `@Provides` / `@Binds` wiring |
| **Navigation** | `navigation/` | Route constants, `NavHost` graph |

## Repository layer

| Interface | Implementation | Backing store |
|-----------|----------------|---------------|
| `HealthRepository` | `HealthRepositoryImpl` | Retrofit `GET /health` + in-memory cache |
| `CalibrationRepository` | `CalibrationRepositoryImpl` | Retrofit calibration endpoints |
| `LiveStreamRepository` | `LiveStreamRepositoryImpl` | `LiveStreamWebSocketManager` (OkHttp WS) |
| `SettingsRepository` | `SettingsRepositoryImpl` | DataStore `cereqon_settings` + `ServerUrlStore` |
| `InsightsRepository` | `InsightsRepositoryImpl` | Room `SessionDao`, `WindowSnapshotDao` |

## Data sources

| Source | Technology | Used by |
|--------|------------|---------|
| REST API | Retrofit + kotlinx.serialization | Health, Calibration |
| Live stream | OkHttp WebSocket `/ws/live` | Dashboard (owner), Calibration (owner), Insights (read-only) |
| Preferences | DataStore | Settings, onboarding flags |
| Local cache | Room `cereqon.db` | Insights (sessions, window snapshots) |

## WebSocket stream ownership

`LiveStreamWebSocketManager` is a singleton. Exactly one feature ViewModel drives `start()` / `stop()` at a time.

| Feature | Role | Calls `start()` / `stop()` | Persists to Room |
|---------|------|---------------------------|------------------|
| **Dashboard** | Stream owner during monitoring | Yes — init, refresh, `onCleared` | Yes — `recordWindowSnapshot` per window |
| **Calibration** | Stream owner during baseline collection | Yes — calibration flow, `onCleared` | Yes — calibration session snapshots |
| **Insights** | Read-only observer | **No** — observes `connectionState` only | **No** — reads Room via reactive `Flow` |

Navigation `popUpTo { inclusive = true }` on onboarding prevents Dashboard and Calibration from coexisting. Insights does not compete for stream control.

## Presentation features

| Feature | Package | ViewModel | Primary repositories |
|---------|---------|-----------|---------------------|
| Welcome | `presentation/welcome/` | `WelcomeViewModel` | `HealthRepository`, `SettingsRepository` |
| Calibration | `presentation/calibration/` | `CalibrationViewModel` | `LiveStreamRepository`, `CalibrationRepository`, `InsightsRepository` |
| Dashboard | `presentation/dashboard/` | `DashboardViewModel` | `LiveStreamRepository`, `SettingsRepository`, `InsightsRepository` |
| Insights | `presentation/insights/` | `InsightsViewModel` | `InsightsRepository`, `LiveStreamRepository` (observe), `SettingsRepository` |

## Shared presentation primitives

| Type | Package | Purpose |
|------|---------|---------|
| `LoadableUiState<T>` | `presentation/state/` | Idle / Loading / Success / Error for async content |
| `OfflineUiState` | `presentation/state/` | Online / offline-with-cache / offline-no-cache |
| `ConnectionUiState` | `presentation/state/` | Defined; not used in screens yet |
| `ErrorUiState` | `presentation/state/` | Defined; not used in screens yet |

## Application entry

- `CereqonApp` — `@HiltAndroidApp`; preloads server URL on `IoDispatcher` at startup.
- `MainActivity` — `@AndroidEntryPoint`; hosts `CereqonNavHost` inside `CereqonTheme`.

## Design constraints

- Backend contract is fixed (`nurolab/app_backend/server.py`); no client-side API invention.
- Dashboard displays raw backend values only; no client analytics on the live path.
- `BrainMetrics` exists in domain for future client-side computation; not used in Dashboard or Insights architecture.
- Room schema includes `calibration_attempts` and `reports` tables; only session/window tables are wired through `InsightsRepository` today.

## Phase status

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Infrastructure, data layer, theme | Complete |
| 2 | Rebrand + Welcome | Complete |
| 3 | Calibration | Complete |
| 4 | Dashboard (foundation → polish) | Complete |
| 5A | Insights architecture (Room read path, no UI) | Partial |
| 5B+ | Insights UI, Dashboard nav, Reports export | Planned |
