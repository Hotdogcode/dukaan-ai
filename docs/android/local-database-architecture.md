# Local Database Architecture (Room)

## 1. Overview
The local SQLite database in [`:core:database`](file:///c:/Dukan-AI/android/core/database) represents the **authoritative single source of truth** for DukaanAI's offline-first architecture. All transaction entries, product lookups, customer khata balances, and sync outbox events persist locally before cloud synchronization.

## 2. Configuration & Components

### 2.1 Database Definition (`DukaanDatabase`)
- Database Name: `dukaanai.db`
- Current Version: `1`
- Built using `Room.databaseBuilder()` in `DatabaseModule.kt` and provided as a `@Singleton` dependency.

### 2.2 Deterministic Type Converters
To prevent IEEE 754 floating-point inaccuracies and support modern domain types:
- **`BigDecimalConverter`**: Financial values are serialized to and from plain text strings (`amount.toPlainString()`). This guarantees zero precision or rounding loss during SQLite persistence.
- **`InstantConverter`**: Timestamps are stored as epoch milliseconds (`Long`).
- **`UuidConverter`**: Tenant, store, product, and transaction UUIDs are stored as canonical hyphenated strings (`uuid.toString()`).

### 2.3 Foundation Entity: `AppMetadataEntity`
A baseline key-value table (`app_metadata`) persists system metadata (e.g. schema sync state, device installation tokens, baseline flags) and validates Room compiler code generation and DAO query execution.

## 3. Schema Migration Strategy
As DukaanAI introduces products, sales journals, inventory ledgers, and khata records in subsequent stages:
1. **Incremental Schema Versions**: Every schema modification increments `version` in `DukaanDatabase`.
2. **Explicit Migration Objects**: Destructive migrations (`fallbackToDestructiveMigration()`) are **strictly prohibited** in production to prevent data loss on retailers' devices.
3. **Migration Pattern**:
   ```kotlin
   val MIGRATION_1_2 = object : Migration(1, 2) {
       override fun migrate(db: SupportSQLiteDatabase) {
           db.execSQL("CREATE TABLE IF NOT EXISTS products (...)")
       }
   }
   ```
4. **Automated Migration Testing**:
   Every schema migration will be verified using `androidx.room.testing.MigrationTestHelper` before deployment.

## 4. DAO Testing Infrastructure
Room DAO tests run deterministically using in-memory databases (`Room.inMemoryDatabaseBuilder`) and Robolectric:
- Zero dependency on physical devices or Android emulators.
- Executes on the developer machine in milliseconds.
- Each test runs in an isolated SQLite instance and closes cleanly upon test completion.
