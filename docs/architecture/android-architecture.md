# DukaanAI: Android Architecture

## 1. High-Level Android Architecture

DukaanAI Android application is engineered as a **modular, offline-first native client** adhering to **Clean Architecture** and **Unidirectional Data Flow (UDF)** principles.

```
+-------------------------------------------------------------------------------+
|                                UI / Feature Layer                             |
|  - Jetpack Compose Screens, Material 3 Components, Navigation Compose         |
|  - ViewModels observing StateFlow, emitting immutable UiState                 |
+-------------------------------------------------------------------------------+
                                        | (depends on)
                                        v
+-------------------------------------------------------------------------------+
|                                  Domain Layer                                 |
|  - Pure Kotlin business models (no Android framework dependencies)           |
|  - Use Cases / Interactors executing single business operations               |
|  - Repository Interfaces (ports)                                              |
|  - Deterministic Math Engine (BigDecimal financial calculations)             |
+-------------------------------------------------------------------------------+
                                        | (implemented by)
                                        v
+-------------------------------------------------------------------------------+
|                                  Data Layer                                   |
|  - Repository Implementations                                                 |
|  - Local Data Source: Room Database (SQLite), DataStore Preferences           |
|  - Remote Data Source: Retrofit, OkHttp, Kotlinx Serialization                |
|  - Sync Engine: WorkManager, Outbox sync worker                               |
+-------------------------------------------------------------------------------+
```

---

## 2. Modularization Strategy

```
android/
├── app/                      # Application entry point, Application class, top-level navigation
├── core/
│   ├── common/               # Dispatchers, result wrappers, date/currency utilities, base classes
│   ├── designsystem/         # Material 3 theme, colors, typography, reusable composables
│   └── model/                # Core domain models, enums, value objects (Money, TenantId, ProductId)
├── feature/
│   ├── pos/                  # Counter billing & barcode scanning UI (deferred)
│   ├── inventory/            # Product catalog, stock adjustments & audits (deferred)
│   ├── khata/                # Customer credit ledger & payment recording (deferred)
│   └── analytics/            # Profit/loss & business insight charts (deferred)
├── domain/                   # Business use cases & calculation invariants
├── ai/                       # Voice capture, on-device audio preprocessing & AI client
└── build-logic/              # Gradle convention plugins for consistent build configs
```

### Module Dependency Rules
1. `feature/*` modules may depend on `core/*` and `domain`.
2. `feature/*` modules **never** depend on other `feature/*` modules. Navigation between features is orchestrated via deep links or navigation interfaces in `app`.
3. `domain` has **zero** dependencies on Android SDK packages (`android.*`). It is pure Kotlin.
4. `core/model` holds shared value objects across all layers.

---

## 3. UI Layer (Jetpack Compose & Material 3)

- **Declarative UI**: 100% Jetpack Compose with Material 3 theming.
- **Unidirectional Data Flow (UDF)**:
  - `UiState`: Data class representing everything the screen needs to render.
  - `UiEvent`: Sealed interface representing user actions (e.g., `AddProductClicked`, `RecordPaymentConfirmed`).
  - `UiEffect`: One-shot side-effects (e.g., `NavigateToReceipt`, `ShowSnackbar`).
- **Screen Architecture**:
  ```kotlin
  @Composable
  fun PosRoute(
      viewModel: PosViewModel = hiltViewModel(),
      onNavigateToCheckout: (orderId: String) -> Unit,
  ) {
      val uiState by viewModel.uiState.collectAsStateWithLifecycle()
      PosScreen(
          uiState = uiState,
          onEvent = viewModel::onEvent,
      )
  }
  ```

---

## 4. State & Dependency Management

- **Dependency Injection**: Google Hilt (`@HiltAndroidApp`, `@AndroidEntryPoint`, `@HiltViewModel`).
- **Concurrency**: Kotlin Coroutines with structured concurrency (`viewModelScope`).
- **Reactive Streams**: `StateFlow` for state observation; `SharedFlow` for one-time channel events.

---

## 5. Offline-First Data Architecture

- **Single Source of Truth**: The local Room database is always the source of truth for the UI.
- **Reading Data**: Screens observe Room queries as `Flow<T>`. When network sync occurs in the background, Room updates and automatically emits new state to the UI.
- **Writing Data**:
  1. Transaction written to local Room tables.
  2. Sync event written to local `outbox_events` table in the same SQLite transaction.
  3. WorkManager picks up pending outbox events, pushes to FastAPI backend with `idempotency_key`, and marks events as synced upon 200 OK.

---

## 6. Financial Representation & Precision

- Every monetary amount in Android code uses `java.math.BigDecimal` or a dedicated value class:
  ```kotlin
  @JvmInline
  value class MonetaryAmount(val amount: BigDecimal) {
      operator fun plus(other: MonetaryAmount): MonetaryAmount =
          MonetaryAmount(amount.add(other.amount))
  }
  ```
- Floating point primitives (`Float`, `Double`) are strictly forbidden for pricing, taxes, ledger credits, or stock quantities.
