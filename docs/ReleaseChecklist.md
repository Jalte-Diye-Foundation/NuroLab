# Cereqon Android — Release Checklist

**Package:** `org.jaltediye.cereqon` · **Version:** 1.0.0 (1)  
**Last audit:** 2026-07-03

---

## 1. Release signing

| Item | Status | Notes |
|------|--------|-------|
| Upload keystore (`release-keystore.jks`) | Local | Gitignored; generate via `scripts/generate-release-keystore.ps1` |
| `keystore.properties` | Local | Copy from `keystore.properties.example`; never commit |
| `signingConfigs.release` in `app/build.gradle.kts` | Done | Loads from `keystore.properties` when present |
| Play App Signing | Manual | Enroll in Play Console; upload this key as **upload key** |
| Signed APK | **Verified** | `app/build/outputs/apk/release/app-release.apk` (~2.0 MB); apksigner v2 ✓ |
| Signed AAB | **Verified** | `app/build/outputs/bundle/release/app-release.aab` (~3.9 MB) |
| ProGuard/R8 mapping | **Verified** | `app/build/outputs/mapping/release/mapping.txt` (~31 MB) — upload to Play Console per release |

### Generate keystore (one-time)

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
cd android
copy keystore.properties.example keystore.properties
# Edit keystore.properties with strong passwords
.\scripts\generate-release-keystore.ps1
```

### Release build

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
.\gradlew assembleRelease bundleRelease
```

Verify signing (APK Signature Scheme v2):

```powershell
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
$apksigner = Get-ChildItem "$sdk\build-tools" -Recurse -Filter apksigner.bat | Sort-Object FullName -Descending | Select-Object -First 1
& $apksigner.FullName verify --verbose app\build\outputs\apk\release\app-release.apk
```

---

## 2. Production security

| Item | Status | Notes |
|------|--------|-------|
| Cleartext traffic (release) | Pass | `network_security_config.xml` — `cleartextTrafficPermitted="false"` |
| Cleartext traffic (debug) | Pass | `src/debug/res/xml/network_security_config.xml` — allowed for emulator/local backend |
| Network Security Config linked | Pass | `android:networkSecurityConfig` on `<application>` |
| Exported components | Pass | Only `MainActivity` exported (launcher); library components use merger defaults |
| Permissions | Pass | `INTERNET`, `ACCESS_NETWORK_STATE` only |
| Backup rules | Pass | `backup_rules.xml` excludes DB, DataStore prefs, reports |
| Data extraction rules | Pass | `data_extraction_rules.xml` excludes same sensitive paths |
| HTTP logging (release) | Pass | `HttpLoggingInterceptor.Level.NONE` when not `BuildConfig.DEBUG` |
| Default server URL (release) | Pass | `DEFAULT_SERVER_BASE_URL=""` — user must configure in Settings |

---

## 3. Performance (code review)

| Area | Assessment |
|------|------------|
| Startup | Hilt singleton graph; no heavy work in `Application.onCreate` |
| Memory | WebSocket buffer 64; dashboard history capped in ViewModel |
| Battery | WebSocket stops when repository `stop()` called; OkHttp ping 30s |
| Compose recomposition | State hoisted to ViewModels; `collectAsStateWithLifecycle` in UI |
| WebSocket lifecycle | `@Singleton` manager; exponential backoff reconnect while started |

**Manual:** Profile startup with Android Studio Profiler on signed release APK.

---

## 4. Stability (manual QA on signed release)

| Scenario | Verify |
|----------|--------|
| Rotation | Dashboard/Settings survive rotation; ViewModel retains state |
| Process death | Room persists sessions; WebSocket reconnects after restart |
| Background / foreground | Stream pauses/resumes per repository lifecycle |
| Offline mode | Connection state → RECONNECTING / FAILED; user-visible error |
| Reconnect | Backoff reconnect while dashboard active |
| Room persistence | Sessions and snapshots survive app restart |

---

## 5. Pre-upload artifacts checklist

- [ ] Signed AAB uploaded to Play Console (internal track first)
- [ ] `mapping.txt` uploaded for this versionCode
- [ ] Version code incremented for each store upload
- [ ] Release notes prepared
- [ ] Privacy policy URL live (`https://www.jaltediye.org/privacy`)
- [ ] Smoke test on physical device (Welcome → Calibration → Dashboard → Settings)
- [ ] Backend reachable over **HTTPS** / **WSS** (release blocks cleartext)

---

## Known non-blockers (out of scope for release engineering)

- No automated unit/instrumentation tests
- Insights / Reports routes registered but no Dashboard navigation entry
- Room uses `fallbackToDestructiveMigration()` — acceptable for v1.0.0; add migrations before schema changes
- Onboarding always starts at Welcome screen
