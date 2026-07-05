# Cereqon Android — NuroLab → Cereqon Migration Plan

This document records the approved rebrand from **NuroLab Android** to **Cereqon**. Backend Python services remain under `nurolab/` and are **unchanged** for API compatibility.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Android app display name, package, theme | Python backend rename |
| Gradle project name | REST/WebSocket paths (`/health`, `/ws/live`, etc.) |
| Kotlin package `org.jaltediye.cereqon` | JSON field names in DTOs |
| Android README & docs | Backend repository folder name `NuroLab/` |
| Launcher icon & Compose theme | ML model files |

## Identity mapping

| Before | After |
|--------|-------|
| App name `NuroLab` | `Cereqon` |
| `applicationId` / `namespace` `com.nurolab.app` | `org.jaltediye.cereqon` |
| `NurolabApp` | `CereqonApp` |
| `Theme.NuroLab` | `Theme.Cereqon` |
| `NurolabTheme` | `CereqonTheme` |
| Gradle `rootProject.name = "NuroLab"` | `"Cereqon"` |
| DataStore `nurolab_settings` | `cereqon_settings` |
| Room DB `nurolab.db` | `cereqon.db` |

## Internal rename (backend-compatible)

These Kotlin types were renamed for product consistency. **HTTP paths and DTO JSON keys are unchanged.**

| Before | After |
|--------|-------|
| `NurolabApiService` | `BackendApiService` |
| `NurolabDtos.kt` | `BackendDtos.kt` |
| `NurolabMappers.kt` | `BackendMappers.kt` |
| `NurolabBackendDefaults` | `BackendDefaults` |
| `NurolabDatabase` | `CereqonDatabase` |

## Migration steps (executed)

1. **Copy** source tree `com/nurolab/app/` → `org/jaltediye/cereqon/`.
2. **Update** all `package` declarations and imports.
3. **Rename** application, database, and API wrapper classes (see tables above).
4. **Update** `AndroidManifest.xml`, `build.gradle.kts`, `settings.gradle.kts`, `strings.xml`, `themes.xml`.
5. **Replace** launcher icon vector with Cereqon brand mark.
6. **Apply** Cereqon Material 3 color system (see `docs/BRAND.md`).
7. **Implement** Phase 2 Welcome screen + NavHost (Welcome only).
8. **Remove** old `com/nurolab/` package directory.
9. **Verify** Gradle sync and Hilt/Room/KSP code generation with new namespace.

## Backend compatibility checklist

- [x] `GET /health` unchanged
- [x] `GET /calibration/status` unchanged
- [x] `POST /calibration/build_baseline` unchanged
- [x] WebSocket `/ws/live` unchanged
- [x] Default emulator URL `http://10.0.2.2:8000/` unchanged
- [x] Feature vector size (104) and channel defaults unchanged

## Post-migration notes

- **Clean install recommended** after package change (`applicationId` change breaks in-place upgrade from `com.nurolab.app`).
- **Room** uses `fallbackToDestructiveMigration()` — local DB resets on schema/name change (acceptable for pre-release).
- **Phase 3** will register `Routes.CALIBRATION` in `CereqonNavHost`; Welcome `Continue` persists server URL and marks setup complete.

## Rollback

Revert to commit before migration and restore `com.nurolab.app` package. Backend requires no rollback.
