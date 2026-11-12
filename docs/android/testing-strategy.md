# Testing Strategy & Verification

## 1. Overview
DukaanAI enforces deterministic, fast, and hermetic automated testing across all layers. Tests are designed to run on development workstations without requiring an active Android emulator or physical device.

## 2. Test Architecture & Conventions

### 2.1 Testing Pyramid
```
             / \
            /   \      Compose UI Tests (Robolectric / Instrumented)
           /-----\
          /       \    Integration Tests (Room DAOs, Repository Impls)
         /---------\
        /           \  Unit Tests (ViewModels, Use Cases, Math Engines)
       /-------------\
```

### 2.2 ViewModel Testing (Turbine & MainDispatcherRule)
- **`MainDispatcherRule`** ([`:core:testing/rule/MainDispatcherRule.kt`](file:///c:/Dukan-AI/android/core/testing/src/main/java/ai/dukaan/core/testing/rule/MainDispatcherRule.kt)):
  Replaces `Dispatchers.Main` with a `TestDispatcher` (e.g. `UnconfinedTestDispatcher`) to execute coroutines synchronously in unit tests.
- **Turbine**:
  Turbine provides reactive assertion over `StateFlow` emissions:
  ```kotlin
  viewModel.uiState.test {
      val state = awaitItem()
      assertEquals(SplashUiState.Success(SplashTarget.LOGIN), state)
  }
  ```

### 2.3 Repository Testing
- Repositories are tested using MockK or dedicated test doubles (e.g. `FakeAppConfigRepository`, `FakeConnectivityRepository` located in `:core:testing`).

### 2.4 Room DAO Testing (In-Memory SQLite with Robolectric)
- Room tests extend `AndroidJUnit4` and run on local JVM via Robolectric:
  ```kotlin
  db = Room.inMemoryDatabaseBuilder(context, DukaanDatabase::class.java)
      .allowMainThreadQueries()
      .build()
  ```
- Ensures SQL queries, index constraints, and TypeConverters execute against real SQLite bytecode without emulator overhead.

### 2.5 Compose UI Testing
- `createComposeRule()` runs in local JVM tests with Robolectric:
  ```kotlin
  composeTestRule.setContent {
      DukaanPrimaryButton(text = "Confirm", onClick = { clicked = true })
  }
  composeTestRule.onNodeWithText("Confirm").assertIsDisplayed().performClick()
  ```

## 3. How to Run Tests
```bash
# Run all unit tests across all modules
./gradlew testDebugUnitTest

# Run tests for a specific module
./gradlew :feature:auth:testDebugUnitTest
./gradlew :core:database:testDebugUnitTest
./gradlew :core:data:testDebugUnitTest
```
