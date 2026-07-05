# Cereqon Android — Navigation

## Graph overview

```
                    startDestination
                          │
                          ▼
                    ┌──────────┐
                    │  WELCOME │
                    └────┬─────┘
                         │ onNavigateToCalibration
                         │ popUpTo(WELCOME) inclusive
                         ▼
                  ┌──────────────┐
                  │ CALIBRATION  │
                  └──────┬───────┘
                         │ onNavigateToDashboard
                         │ popUpTo(CALIBRATION) inclusive
                         ▼
                  ┌──────────────┐
                  │  DASHBOARD   │─── Settings (implemented)
                  └──────────────┘

    Registered in NavHost but no navigate() from any screen:
                  ┌──────────────┐
                  │   INSIGHTS   │  InsightsNavigationEntry (no UI)
                  └──────────────┘
                  ┌──────────────┐
                  │   REPORTS    │  ReportsNavigationEntry (no nav trigger)
                  └──────────────┘
```

## Route constants

Defined in `navigation/Routes.kt`:

| Constant | Value | NavHost | Screen |
|----------|-------|---------|--------|
| `WELCOME` | `"welcome"` | Yes | `WelcomeScreen` |
| `CALIBRATION` | `"calibration"` | Yes | `CalibrationScreen` |
| `DASHBOARD` | `"dashboard"` | Yes | `DashboardScreen` |
| `INSIGHTS` | `"insights"` | Yes | `InsightsNavigationEntry` (no screen UI) |
| `REPORTS` | `"reports"` | Yes | `ReportsNavigationEntry` (no nav trigger) |
| `SETTINGS` | `"settings"` | Yes | `SettingsNavigationEntry` (from Dashboard) |

## NavHost configuration

File: `navigation/CereqonNavHost.kt`

```kotlin
NavHost(
    navController = navController,
    startDestination = Routes.WELCOME,
) { ... }
```

- Single `NavHost` in `MainActivity` via `CereqonNavHost()`.
- No nested navigation graphs.
- No bottom navigation bar.
- No deep links configured.

## Navigation triggers

| From | To | Mechanism |
|------|-----|-----------|
| Welcome | Calibration | `WelcomeScreen(onNavigateToCalibration)` after Continue |
| Calibration | Dashboard | `CalibrationEvent.NavigateToDashboard` collected in screen |

### Welcome navigation

```kotlin
navController.navigate(Routes.CALIBRATION) {
    popUpTo(Routes.WELCOME) { inclusive = true }
}
```

### Calibration navigation

```kotlin
navController.navigate(Routes.DASHBOARD) {
    popUpTo(Routes.CALIBRATION) { inclusive = true }
}
```

## One-shot navigation events

Calibration uses a `Channel` instead of putting navigation flags in UiState:

```kotlin
sealed interface CalibrationEvent {
    data object NavigateToDashboard : CalibrationEvent
}
```

Screen collects:

```kotlin
LaunchedEffect(Unit) {
    viewModel.events.collect { event ->
        when (event) {
            CalibrationEvent.NavigateToDashboard -> onNavigateToDashboard()
        }
    }
}
```

## Insights navigation entry (Phase 5A)

```kotlin
composable(Routes.INSIGHTS) {
    InsightsNavigationEntry()
}
```

- Route is registered for DI/lifecycle scaffolding.
- `DashboardScreen` accepts `onNavigateToInsights` but **does not call it** — no navigation path from the UI.
- Deep link to test: `adb shell am start -a android.intent.action.VIEW -d "cereqon://insights"` — **not configured** (would require manifest intent-filter).

## Planned navigation (not implemented)

| Item | Description |
|------|-------------|
| Onboarding gate | Route to Dashboard/Calibration based on `SettingsRepository.onboardingCompleted` |
| Dashboard → Insights | Wire `onNavigateToInsights` in Dashboard UI |
| Reports export UI | Connect `ReportsViewModel.exportSession*` to `ReportsScreen` |
| Bottom nav | Dashboard ↔ Insights ↔ Reports |
| Back stack | Allow returning to Dashboard from Insights without clearing stack |

## Navigation dependencies

| Artifact | Version source |
|----------|----------------|
| `androidx.navigation:navigation-compose` | Compose BOM |
| `androidx.hilt:hilt-navigation-compose` | `hiltViewModel()` in composables |

## Screen → ViewModel mapping

| Route | Composable | ViewModel |
|-------|------------|-----------|
| `welcome` | `WelcomeScreen` | `WelcomeViewModel` |
| `calibration` | `CalibrationScreen` | `CalibrationViewModel` |
| `dashboard` | `DashboardScreen` | `DashboardViewModel` |
| `insights` | `InsightsNavigationEntry` | `InsightsViewModel` |
