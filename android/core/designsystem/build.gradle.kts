plugins {
    id("dukaanai.android.library.compose")
}

android {
    namespace = "ai.dukaan.core.designsystem"
}

dependencies {
    implementation(project(":core:common"))

    testImplementation(project(":core:testing"))
    testImplementation(libs.junit)
    testImplementation(libs.robolectric)
    testImplementation(libs.androidx.test.ext.junit)
    testImplementation(libs.androidx.compose.ui.test.junit4)
    testImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}
