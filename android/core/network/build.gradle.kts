plugins {
    id("dukaanai.android.library")
    id("dukaanai.android.hilt")
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "ai.dukaan.core.network"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:model"))

    implementation(libs.retrofit.core)
    implementation(libs.retrofit.converter.kotlinx.serialization)
    implementation(libs.okhttp.core)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.timber)
}
