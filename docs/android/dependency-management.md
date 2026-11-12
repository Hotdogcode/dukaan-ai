# Dependency Management & Build Logic

## 1. Centralized Gradle Version Catalog
All library dependencies, testing frameworks, and build plugins are declared centrally in [`android/gradle/libs.versions.toml`](file:///c:/Dukan-AI/android/gradle/libs.versions.toml). Individual module `build.gradle.kts` files must never declare hardcoded string dependency coordinates or disparate versions.

### Key Version Catalog Categories
- **Build & Tooling**: Android Gradle Plugin (AGP `8.7.2`), Kotlin (`2.0.21`), KSP (`2.0.21-1.0.28`).
- **AndroidX & Compose**: Compose BOM (`2024.10.01`), Lifecycle (`2.8.7`), Activity Compose (`1.9.3`), Navigation Compose (`2.8.3`).
- **Dependency Injection**: Google Hilt (`2.52`), Hilt Navigation Compose (`1.2.0`), Hilt Work (`1.2.0`).
- **Data & Concurrency**: Room (`2.6.1`), DataStore (`1.1.1`), Coroutines (`1.9.0`), WorkManager (`2.10.0`).
- **Networking**: Retrofit (`2.11.0`), OkHttp (`4.12.0`), Kotlinx Serialization (`1.7.3`).
- **Testing**: JUnit 4, Robolectric (`4.14.1`), MockK (`1.13.13`), Turbine (`1.2.0`), Compose UI Test JUnit 4.

## 2. Convention Plugins under `build-logic`
To eliminate boilerplate across Android modules, DukaanAI utilizes custom Gradle convention plugins located in [`android/build-logic`](file:///c:/Dukan-AI/android/build-logic):

| Plugin ID | Class Name | Applied Capabilities |
| :--- | :--- | :--- |
| `dukaanai.android.library` | `AndroidLibraryConventionPlugin` | Configures Android Library, Kotlin Android, Compile SDK 35, Min SDK 26, Java 21, JVM 21, JUnit |
| `dukaanai.android.library.compose` | `AndroidLibraryComposeConventionPlugin` | Extends `dukaanai.android.library` with Compose compiler, Compose BOM, Material 3, Preview |
| `dukaanai.android.feature` | `AndroidFeatureConventionPlugin` | Applies Compose + Hilt, automatically links `:core:model`, `:core:designsystem`, `:core:ui`, `:core:navigation`, `:core:domain`, and ViewModel Compose |
| `dukaanai.android.hilt` | `AndroidHiltConventionPlugin` | Applies Hilt plugin + KSP compiler dependencies |
| `dukaanai.android.room` | `AndroidRoomConventionPlugin` | Applies KSP, Room runtime, Room KTX, Room compiler, Room testing |
| `dukaanai.jvm.library` | `JvmLibraryConventionPlugin` | Configures pure Kotlin JVM library (no Android SDK) with Java 21 and Coroutines |

## 3. Compiler Options & Target Compatibility
Every Android and JVM module strictly targets **Java 21 / JVM 21**:
```kotlin
compileOptions {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}
kotlinOptions {
    jvmTarget = "21"
}
```

## 4. How to Add a New Dependency
1. **Declare version & coordinate in `libs.versions.toml`**:
   ```toml
   [versions]
   foo = "1.2.3"

   [libraries]
   foo-core = { group = "com.example.foo", name = "foo-core", version.ref = "foo" }
   ```
2. **Reference type-safely in module `build.gradle.kts`**:
   ```kotlin
   dependencies {
       implementation(libs.foo.core)
   }
   ```
3. **Never add dependencies without architectural justification**.

## 5. Dependency Verification Strategy
- **Reproducible Builds**: All dependencies are locked through the version catalog.
- **Gradle Dependency Verification**: Gradle checksum verification metadata can be generated with:
  ```bash
  ./gradlew --write-verification-metadata sha256 help
  ```
  This creates `gradle/verification-metadata.xml` to prevent dependency tampering or supply-chain man-in-the-middle attacks during CI/CD.
