plugins {
    id("dukaanai.android.library")
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "ai.dukaan.core.navigation"
}

dependencies {
    implementation(libs.androidx.navigation.compose)
    implementation(libs.kotlinx.serialization.json)
}
