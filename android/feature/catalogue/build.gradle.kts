plugins {
    id("dukaanai.android.feature")
}

android {
    namespace = "ai.dukaan.feature.catalogue"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:domain"))
    implementation(project(":core:model"))
    implementation(project(":core:data"))

    // CameraX for Barcode Scanning
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)

    // Google ML Kit Barcode Scanning
    implementation(libs.google.mlkit.barcode.scanning)

    // Material Icons Extended & Coil
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.coil.compose)

    testImplementation(project(":core:testing"))
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.mockk)
    testImplementation(libs.turbine)
}
