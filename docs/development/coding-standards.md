# DukaanAI: Engineering & Coding Standards

## 1. General Principles

1. **Clarity Over Cleverness**: Code is read ten times more often than it is written. Prefer readable, self-explanatory code over complex abstractions.
2. **Explicit Contracts**: Functions, APIs, and data models must specify explicit types and nullability constraints.
3. **Fail Fast & Deterministically**: Validate preconditions early. Return strongly typed errors (`Result<T, E>`) rather than throwing raw runtime exceptions.

---

## 2. Android (Kotlin & Jetpack Compose) Standards

### 2.1 Kotlin Language Rules
- **Null Safety**: Never use force unwrap (`!!`). Use safe calls (`?.`), `let`, or Elvis operator (`?:`).
- **Immutability**: Prefer `val` over `var`. Default to immutable collections (`List`, `Set`, `Map`).
- **Data Models**: Use data classes or `@JvmInline value class` for primitives with semantic meaning (e.g., `TenantId`, `Money`).
- **Monetary Values**: Always use `java.math.BigDecimal`. Never use `Float` or `Double` for currency or inventory quantities.

### 2.2 Jetpack Compose Guidelines
- **Stateless Composables**: Separate stateful screen wrappers (observing ViewModel) from stateless UI composables (accepting data class and lambda callbacks).
- **Naming**:
  - Screen containers: `[Feature]Route` (e.g., `PosRoute`).
  - Pure UI components: `[Feature]Screen` or `[Component]Widget` (e.g., `PosScreen`, `TransactionCard`).
- **Modifiers**: Always accept an optional `modifier: Modifier = Modifier` as the first optional parameter and chain it to the root layout element.
- **Preview Support**: Every stateless composable should provide at least one `@Preview` demonstrating light and dark theme appearance.

### 2.3 ViewModel & State Flow Rules
- ViewModels expose a single `val uiState: StateFlow<UiState>` using `.stateIn(...)` with `SharingStarted.WhileSubscribed(5_000)`.
- Never expose mutable state flows (`MutableStateFlow`) publicly.
- Business operations must be executed via domain Use Cases, not directly in ViewModels.

---

## 3. Backend (Python & FastAPI) Standards

### 3.1 Python 3.12 Conventions
- **Strict Typing**: All function signatures must have full type annotations (`def get_balance(customer_id: UUID) -> Decimal:`).
- **Modern Syntax**: Use native union syntax (`str | None`), built-in generic collections (`list[str]`, `dict[str, Any]`).
- **Code Style**: Follow PEP 8 and use `ruff` for linting and formatting (line length: 88 characters).

### 3.2 FastAPI & Pydantic Guidelines
- **Input Validation**: All request bodies and query parameters must be validated via Pydantic v2 `BaseModel` classes with `ConfigDict(frozen=True)` where appropriate.
- **Dependency Injection**: Use `Depends(...)` for database sessions, authentication context, and tenant resolution.
- **Error Handling**: Use custom HTTPException handlers returning consistent JSON error envelopes:
  ```json
  {
    "error_code": "INSUFFICIENT_STOCK",
    "message": "Available stock is less than requested quantity.",
    "details": { "product_id": "...", "available": 2 }
  }
  ```

### 3.3 Database & Financial Math
- Use `decimal.Decimal` for all arithmetic calculations.
- Always use async database drivers (`asyncpg`) and async SQLAlchemy session contexts.
- Every mutating transaction must occur within an atomic session context block.

---

## 4. Git & Commit Conventions

Follow the **Conventional Commits** specification:
```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Types:
- `feat`: New product capability or business feature.
- `fix`: Bug fix.
- `docs`: Documentation updates only.
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `test`: Adding or updating tests.
- `chore`: Build system, dependencies, or tooling adjustments.

### Examples:
- `feat(pos): add barcode scanner support for counter checkout`
- `fix(ledger): correct decimal rounding in customer balance aggregate`
- `docs(api): document sync endpoint contract and idempotency behavior`

---

## 5. Testing Requirements

- **Domain Logic**: 100% unit test coverage for mathematical calculation engines (tax, discounts, stock balance, ledger reconciliation).
- **Backend API**: Every FastAPI endpoint must have corresponding async integration tests in `backend/tests/`.
- **Android UI**: Compose tests for critical paths (Counter POS, Voice Confirmation dialog).
