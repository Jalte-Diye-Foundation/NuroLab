# Cereqon — Play Store Readiness Checklist

**App ID:** `org.jaltediye.cereqon`  
**Target:** Google Play (production)

---

## A. Google Play Console setup

| # | Task | Status |
|---|------|--------|
| 1 | Create app in Play Console | Manual |
| 2 | Enroll in **Play App Signing** | Manual — Google holds app signing key; you upload with upload key |
| 3 | Upload first **AAB** (`bundleRelease`) | After local keystore + build |
| 4 | Upload **ProGuard mapping** for versionCode 1 | From `mapping/release/mapping.txt` |
| 5 | Complete **Data safety** form | Declare network, local storage (sessions, reports) |
| 6 | Set **Privacy policy** URL | `https://www.jaltediye.org/privacy` |
| 7 | Content rating questionnaire | Complete IARC questionnaire |
| 8 | Target audience & ads declaration | No ads in current build |
| 9 | App access instructions | Provide test server URL / demo account if backend gated |

---

## B. Store listing assets

| Asset | Requirement | Project location |
|-------|-------------|------------------|
| App name | Cereqon | `strings.xml` |
| Short description | ≤ 80 chars | See `docs/BRAND.md` |
| Full description | ≤ 4000 chars | See `docs/BRAND.md` |
| App icon | 512×512 PNG | Export from `@mipmap/ic_launcher` |
| Feature graphic | 1024×500 | Manual design |
| Phone screenshots | ≥ 2 | Capture from release build |
| Tablet screenshots | Optional | If supporting tablets |

---

## C. Technical compliance

| Requirement | Status |
|-------------|--------|
| `targetSdk` 35 | Pass |
| 64-bit native libs (if any) | N/A — no NDK |
| Android App Bundle (AAB) | Required for new apps |
| Cleartext HTTP disabled (release) | Pass |
| No unnecessary permissions | Pass |
| Backup / extraction rules | Pass |
| Signed with upload key | **Verified** (2026-07-03) |

---

## D. Release build commands

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
cd "e:\new labs\NuroLab\android"
.\scripts\generate-release-keystore.ps1   # first time only
.\gradlew clean assembleRelease bundleRelease
```

**Outputs:**

| Artifact | Path |
|----------|------|
| Signed APK | `app/build/outputs/apk/release/app-release.apk` |
| Signed AAB | `app/build/outputs/bundle/release/app-release.aab` |
| Mapping | `app/build/outputs/mapping/release/mapping.txt` |

---

## E. Post-upload verification

- [ ] Internal testing track: install from Play, verify HTTPS backend
- [ ] Pre-launch report: review crashes / security warnings
- [ ] Verify WebSocket stream on production WSS endpoint
- [ ] Confirm Settings → server URL persists across restart
- [ ] Export report files land in app-private storage only

---

## F. Play App Signing workflow

1. Generate **upload keystore** locally (`release-keystore.jks`).
2. Sign AAB with upload key (`signingConfigs.release`).
3. Upload AAB to Play Console.
4. Google re-signs with **app signing key** for distribution.
5. **Backup upload keystore** securely; loss requires Play Console reset process.

Optional: register upload key certificate SHA-1 in Play Console → App integrity.
