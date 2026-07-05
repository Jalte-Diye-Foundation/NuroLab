# Cereqon — Brand Identity System

Premium medical-tech visual language for the Jalte Diye Foundation EEG wellness platform. Quality bar: **Oura · Fitbit · Garmin** — calm, data-rich, trustworthy.

---

## Brand essence

**Cereqon** = cerebral signal clarity + precision monitoring. The product illuminates personal mental state through objective physiology — not diagnosis, but **awareness**.

**Tagline:** *Clarity in every signal.*

---

## Logo concept

**Mark:** A hexagonal **signal node** (six vertices) with a single continuous **EEG waveform** passing through the center horizontal axis. The hex suggests neural network topology; the wave suggests live streaming.

**Wordmark:** `Cereqon` set in geometric sans (see Typography). Lowercase optional for digital; title case for app launcher.

**Clear space:** Minimum padding = height of the letter `o` on all sides.

**Do not:** Use brains, chat bubbles, robot motifs, or stock “AI sparkle” icons.

---

## App icon concept

- **Shape:** Adaptive icon — foreground on `#0F172A` (midnight navy) circular background.
- **Foreground:** Simplified logo mark — white/teal waveform inside indigo hex outline.
- **Accent dot:** Small `#2DD4BF` pulse dot at the right vertex (live signal indicator).
- **Sizes:** Provide vector foreground `@drawable/ic_launcher_foreground`; background `@color/ic_launcher_background`.

---

## Material 3 color palette

### Light theme

| Token | Hex | Usage |
|-------|-----|--------|
| Primary | `#0D9488` | CTAs, active indicators, links |
| On Primary | `#FFFFFF` | Text on primary buttons |
| Primary Container | `#CCFBF1` | Selected chips, soft highlights |
| On Primary Container | `#134E4A` | Text on primary container |
| Secondary | `#6366F1` | Secondary metrics, chart accents |
| On Secondary | `#FFFFFF` | Text on secondary |
| Tertiary | `#F59E0B` | Warm attention (not alarm) |
| Background | `#F8FAFC` | Screen background |
| On Background | `#0F172A` | Primary text |
| Surface | `#FFFFFF` | Cards, sheets |
| On Surface | `#0F172A` | Card text |
| Surface Variant | `#E2E8F0` | Dividers, input borders |
| Outline | `#94A3B8` | Borders |
| Error | `#DC2626` | Connection failures |

### Dark theme

| Token | Hex | Usage |
|-------|-----|--------|
| Primary | `#2DD4BF` | CTAs, live signal |
| On Primary | `#042F2E` | Text on primary |
| Primary Container | `#134E4A` | Elevated chips |
| On Primary Container | `#CCFBF1` | Text on container |
| Secondary | `#818CF8` | Chart series |
| Background | `#0A0F1C` | Screen background |
| On Background | `#F1F5F9` | Primary text |
| Surface | `#151B2E` | Cards |
| On Surface | `#F1F5F9` | Card text |
| Surface Variant | `#1E293B` | Input fields |
| Outline | `#475569` | Borders |
| Error | `#F87171` | Errors |

### Semantic metrics (dashboard — Phase 3+)

| Metric | Color |
|--------|-------|
| Relaxation | `#2DD4BF` |
| Engagement | `#6366F1` |
| Cognitive load | `#F59E0B` |
| Risk tier 0 (baseline) | `#22C55E` |
| Risk tier 1–2 | `#F59E0B` |
| Risk tier 3 | `#EF4444` |

---

## Typography

| Role | Style | Size / Weight |
|------|-------|----------------|
| Display | `headlineLarge` | 32sp · Bold |
| Title | `titleLarge` | 22sp · SemiBold |
| Section | `titleMedium` | 16sp · SemiBold |
| Body | `bodyLarge` | 16sp · Normal |
| Caption | `labelMedium` | 12sp · Medium |
| Metric value | `displaySmall` | 36sp · Medium · tabular nums |
| Metric label | `labelSmall` | 11sp · Medium · uppercase tracking |

**Font family:** System default (Roboto on Android). Future: **Inter** or **DM Sans** bundled in `res/font/` for wordmark parity.

---

## Splash screen

**Duration:** System splash (Android 12+) via `Theme.Cereqon.Splash` → hand off to Welcome.

**Layout:**
- Full-bleed `#0A0F1C` background.
- Centered Cereqon mark (animated scale 0.92 → 1.0, 600ms ease-out).
- Subtle radial gradient glow `#2DD4BF` at 8% opacity behind mark.
- No text on splash (wordmark appears on Welcome).

**Welcome handoff:** Cross-fade 300ms into Welcome hero.

---

## Design language

- **Tone:** Clinical calm — never alarmist; deviations inform, they do not diagnose.
- **Density:** Generous whitespace; one primary action per screen.
- **Motion:** Purposeful — connection pulse (1.2s), card stagger (50ms), button spring on enable.
- **Elevation:** Flat cards with 1dp hairline border (`Surface Variant`) — Oura-style, not heavy shadows.
- **Iconography:** Outlined Material Symbols; 24dp default, 20dp inline.
- **Data display:** Large numerals, small caps labels, sparkline placeholders in cards.

---

## UI style

- **Corners:** 16dp cards, 12dp inputs, 28dp full-width buttons (pill).
- **Inputs:** Filled tonal fields (`surfaceVariant` fill, no harsh boxes).
- **Status chips:** Rounded 8dp — Connected (teal), Checking (amber pulse), Offline (neutral), Error (red).
- **Scaffold:** Edge-to-edge; status bar icons adapt light/dark.

---

## Component style

### Primary button (`CereqonPrimaryButton`)

- Full width, 56dp height, pill shape.
- Enabled: `primary` fill; disabled: `surfaceVariant` at 38% opacity.
- Loading: circular indicator 20dp, `onPrimary` color.

### Secondary button

- Outlined pill, `primary` border 1dp.

### Connection status card

- See Dashboard card pattern below; used on Welcome.

---

## Dashboard card design (Phase 3 reference)

```
┌─────────────────────────────────────┐
│  ● Live                    12:04    │  ← status dot + timestamp
│                                     │
│  Cognitive Load          0.62       │  ← label + large metric
│  ▁▂▃▅▃▂▁▂                          │  ← sparkline (teal/violet)
│                                     │
│  Engagement 0.41   Relaxation 0.78  │  ← secondary metrics row
└─────────────────────────────────────┘
```

- **Card:** `surface` fill, 16dp radius, 1dp `outline` at 12% alpha, 20dp padding.
- **Live indicator:** 8dp circle, `#2DD4BF`, optional 1.2s opacity pulse animation.
- **Risk tier badge:** Top-right pill — color from semantic metrics table.

---

## Welcome screen (Phase 2 — implemented)

- Hero: Cereqon mark + wordmark + tagline.
- Server URL field with validation hint (`http://10.0.2.2:8000/` for emulator).
- **Test connection** chip/card with animated status.
- **Continue** primary button — enabled only after successful health check; saves URL on proceed.

---

## Asset checklist

- [x] `ic_launcher_foreground.xml` — Cereqon mark
- [x] `colors.xml` — launcher background
- [x] Compose `Color.kt` — full M3 tokens
- [ ] Custom font files (future)
- [ ] Marketing wordmark SVG (future)
