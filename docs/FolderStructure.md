# Cereqon Android — Folder Structure

Root: `android/app/src/main/java/org/jaltediye/cereqon/`

```
org.jaltediye.cereqon/
│
├── CereqonApp.kt                 @HiltAndroidApp application class
├── MainActivity.kt               Single-activity Compose host
│
├── di/
│   ├── AppModule.kt              NetworkModule, DatabaseModule, RepositoryModule
│   ├── CoroutineModule.kt        @IoDispatcher, @DefaultDispatcher, @ApplicationScope
│   └── DispatchersQualifiers.kt  Qualifier annotations
│
├── domain/
│   ├── model/
│   │   ├── BaselineResult.kt
│   │   ├── BrainMetrics.kt
│   │   ├── CalibrationStatus.kt
│   │   ├── DeviationSnapshot.kt
│   │   ├── FeatureVector.kt
│   │   ├── HealthStatus.kt
│   │   ├── InsightSession.kt         Phase 5A
│   │   ├── InsightWindowSnapshot.kt  Phase 5A
│   │   ├── LiveWindow.kt
│   │   ├── Outcome.kt
│   │   ├── Prediction.kt
│   │   ├── RiskTier.kt
│   │   └── StreamConnectionState.kt
│   └── repository/
│       ├── CalibrationRepository.kt
│       ├── HealthRepository.kt
│       ├── InsightsRepository.kt     Phase 5A
│       ├── LiveStreamRepository.kt
│       └── SettingsRepository.kt
│
├── data/
│   ├── local/
│   │   ├── database/
│   │   │   └── CereqonDatabase.kt
│   │   ├── dao/
│   │   │   └── CereqonDaos.kt        SessionDao, WindowSnapshotDao, CalibrationAttemptDao, ReportDao
│   │   ├── entity/
│   │   │   └── CereqonEntities.kt
│   │   ├── mapper/
│   │   │   └── InsightsMappers.kt    Phase 5A — entity ↔ domain
│   │   └── preferences/
│   │       └── SettingsRepositoryImpl.kt
│   ├── remote/
│   │   ├── api/
│   │   │   └── BackendApiService.kt
│   │   ├── dto/
│   │   │   └── BackendDtos.kt
│   │   ├── mapper/
│   │   │   └── BackendMappers.kt
│   │   ├── websocket/
│   │   │   └── LiveStreamWebSocketManager.kt
│   │   ├── BackendDefaults.kt
│   │   ├── DynamicBaseUrlInterceptor.kt
│   │   └── ServerUrlStore.kt
│   └── repository/
│       ├── HealthAndCalibrationRepositories.kt
│       ├── InsightsRepositoryImpl.kt   Phase 5A
│       └── LiveStreamRepositoryImpl.kt
│
├── navigation/
│   ├── Routes.kt
│   └── CereqonNavHost.kt
│
└── presentation/
    ├── theme/
    │   ├── Color.kt
    │   ├── Theme.kt
    │   └── Type.kt
    ├── components/
    │   ├── CereqonLogoMark.kt
    │   ├── CereqonPrimaryButton.kt
    │   └── ConnectionStatusCard.kt
    ├── state/
    │   ├── ConnectionUiState.kt
    │   ├── ErrorUiState.kt
    │   ├── LoadableUiState.kt
    │   └── OfflineUiState.kt
    ├── welcome/
    │   ├── WelcomeScreen.kt
    │   ├── WelcomeViewModel.kt
    │   └── WelcomeUiState.kt
    ├── calibration/
    │   ├── CalibrationScreen.kt
    │   ├── CalibrationViewModel.kt
    │   └── CalibrationUiState.kt
    ├── dashboard/
    │   ├── DashboardScreen.kt
    │   ├── DashboardViewModel.kt
    │   ├── DashboardUiState.kt
    │   ├── DashboardTimelineHistory.kt
    │   ├── DashboardConnectionQuality.kt
    │   └── components/
    │       ├── DashboardBackendStatusCard.kt
    │       ├── DashboardCardShell.kt
    │       ├── DashboardChartsSection.kt
    │       ├── DashboardConnectionCard.kt
    │       ├── DashboardEmptyState.kt
    │       ├── DashboardFeatureVectorCard.kt
    │       ├── DashboardLayout.kt
    │       ├── DashboardLineChart.kt
    │       ├── DashboardPredictionCard.kt
    │       ├── DashboardRiskCard.kt
    │       └── DashboardStatusStrip.kt
    └── insights/                     Phase 5A — architecture only, no screen
        ├── InsightsNavigationEntry.kt
        ├── InsightsViewModel.kt
        └── InsightsUiState.kt
```

## Resources

```
app/src/main/res/
├── values/
│   ├── strings.xml
│   ├── colors.xml
│   └── themes.xml
└── xml/
    └── network_security_config.xml
```

## Documentation

```
android/docs/
├── Architecture.md
├── API.md
├── BRAND.md
├── DependencyGraph.md
├── Flow.md
├── FolderStructure.md
├── MIGRATION.md
├── Navigation.md
└── StateManagement.md
```

## Naming conventions

| Layer | Convention | Example |
|-------|------------|---------|
| Screen | `{Feature}Screen.kt` | `DashboardScreen.kt` |
| ViewModel | `{Feature}ViewModel.kt` | `InsightsViewModel.kt` |
| UiState | `{Feature}UiState.kt` | `InsightsUiState.kt` |
| Card/component | `{Feature}{Purpose}.kt` | `DashboardRiskCard.kt` |
| Repository interface | `domain/repository/{Name}Repository.kt` | `InsightsRepository.kt` |
| Repository impl | `data/repository/{Name}RepositoryImpl.kt` | `InsightsRepositoryImpl.kt` |
| Mapper | `data/{layer}/mapper/{Name}Mapper(s).kt` | `InsightsMappers.kt` |
| Route | `Routes.{CONSTANT}` lowercase string | `Routes.INSIGHTS = "insights"` |

## Planned (not yet present)

```
presentation/reports/          Reports feature (route defined only)
presentation/insights/components/   Insights UI (Phase 5B+)
domain/repository/ReportsRepository.kt
```
