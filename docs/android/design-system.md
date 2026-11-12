# Design System & UI Foundation

## 1. Design Philosophy for Indian Retailers
DukaanAI is designed for busy Indian kirana store owners and small merchants. The UI adheres to key principles:
- **Low Cognitive Load**: High-contrast, clean surfaces with zero visual clutter.
- **Large Touch Targets**: All interactive elements (buttons, text fields, action chips) enforce a minimum touch target of **48dp**, accommodating one-handed use during busy store counter operations.
- **Clear Financial Hierarchy**: Currency figures and balances are rendered prominently using bold, monospaced-aligned numerals and Indian numbering formatting (`₹ 1,23,456.00`).
- **Bilingual & Hinglish Readiness**: Typography and layouts accommodate both English and Devanagari (Hindi) text strings without layout truncation or awkward wrapping.

## 2. Color Palette & Tokens
Located in [`:core:designsystem/theme/Color.kt`](file:///c:/Dukan-AI/android/core/designsystem/src/main/java/ai/dukaan/core/designsystem/theme/Color.kt):

| Color Token | Hex Code | Semantic Role |
| :--- | :--- | :--- |
| `PrimarySaffron` | `#E65100` | Primary brand accent representing warmth, energy, and Indian retail identity. |
| `SecondaryTeal` | `#00695C` | Secondary accent representing trust, financial security, and stability. |
| `TertiaryGold` | `#8C6B00` | Accent color for cash ledgers, credit khata, and payment settlements. |
| `SurfaceLight` | `#FFF8F6` | Warm, approachable background surface. |
| `SurfaceDark` | `#1A110F` | Deep dark mode background for nighttime accounting. |

## 3. Spacing and Shapes
- **Spacing Tokens** ([`Spacing.kt`](file:///c:/Dukan-AI/android/core/designsystem/src/main/java/ai/dukaan/core/designsystem/theme/Spacing.kt)):
  - `extraSmall`: 4dp
  - `small`: 8dp
  - `medium`: 12dp
  - `large`: 16dp
  - `extraLarge`: 24dp
  - `huge`: 32dp
  - `giant`: 48dp
- **Shapes** ([`Shape.kt`](file:///c:/Dukan-AI/android/core/designsystem/src/main/java/ai/dukaan/core/designsystem/theme/Shape.kt)):
  - 12dp rounded corners on Cards, Text Fields, and Buttons provide a modern, approachable appearance.

## 4. Reusable UI Components
All standard UI widgets reside in [`:core:designsystem/component/`](file:///c:/Dukan-AI/android/core/designsystem/src/main/java/ai/dukaan/core/designsystem/component/):

1. **`DukaanPrimaryButton` / `DukaanOutlinedButton`**:
   - Enforces 48dp minimum height.
   - Built-in loading state with `CircularProgressIndicator`.
2. **`DukaanTextField`**:
   - Outlined text field with clear label, supporting text, and prominent error states.
3. **`DukaanCard`**:
   - Standard 12dp corner radius and subtle 2dp elevation.
4. **`DukaanLoadingWheel`**:
   - Accessible indeterminate progress indicator.
5. **`DukaanErrorState`**:
   - Full-screen or container error presentation with error icon, explanation, and retry action.
6. **`DukaanEmptyState`**:
   - Empty view illustration, explanatory title, and call-to-action button.
7. **`DukaanScaffold`**:
   - Standardized Material 3 Scaffold with top app bar, snackbar host, floating action button, and window insets handling.
