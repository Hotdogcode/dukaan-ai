# Android Development Guide

## 1. Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux.
- **JDK**: Java Development Kit 21 (JDK 21).
- **Android SDK**: Android API 35 (compileSdk 35, minSdk 26).
- **IDE**: Android Studio Ladybug (2024.2+) or Android Studio Koala.

## 2. Project Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/dukaanai/dukaanai.git
   cd dukaanai/android
   ```
2. Verify SDK location in `local.properties`:
   ```properties
   sdk.dir=C\:\\Users\\<username>\\AppData\\Local\\Android\\Sdk
   ```
3. Sync Gradle project using the Gradle Wrapper:
   ```bash
   ./gradlew.bat --version
   ```

## 3. Building the Application
DukaanAI provides two build variants under the `environment` product flavor:

### Build Development APK
```bash
./gradlew.bat assembleDevDebug
```
The output APK is generated at:
`app/build/outputs/apk/dev/debug/app-dev-debug.apk`

### Build Production Release APK
```bash
./gradlew.bat assembleProdRelease
```

## 4. Running the App on an Android Device

### 4.1 Physical Device Testing (e.g. Samsung Galaxy)
1. On your Samsung device, enable **Developer Options**:
   - Go to **Settings > About Phone > Software Information**.
   - Tap **Build Number** 7 times.
2. Enable **USB Debugging** in **Settings > Developer Options**.
3. Connect the phone to your laptop via USB.
4. Verify the device is recognized by ADB:
   ```bash
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
   ```
5. Install the debug APK:
   ```bash
   ./gradlew.bat installDevDebug
   ```

### 4.2 Connecting to Local FastAPI Backend
- **Android Emulator**: Uses `http://10.0.2.2:8000/` (pre-configured in `dev` flavor).
- **Physical Device**:
  1. Ensure both laptop and phone are on the same Wi-Fi network.
  2. Find laptop local IP: `ipconfig` (e.g. `192.168.1.15`).
  3. Reverse ADB port forwarding so phone accesses `localhost:8000`:
     ```bash
     adb reverse tcp:8000 tcp:8000
     ```
  4. Now requests to `http://localhost:8000/` on the physical device hit your local FastAPI server.

## 5. Running Automated Tests
```bash
# Run all unit and Robolectric tests
./gradlew.bat testDebugUnitTest

# Run specific module tests
./gradlew.bat :core:model:test
./gradlew.bat :feature:auth:test
```
