plugins {
    id("dukaanai.android.library")
}

android {
    namespace = "ai.dukaan.core.testing"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:model"))
    implementation(project(":core:domain"))

    implementation(libs.kotlinx.coroutines.test)
    implementation(libs.junit)
    implementation(libs.mockk)
    implementation(libs.turbine)
}
