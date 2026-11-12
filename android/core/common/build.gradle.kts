plugins {
    id("dukaanai.android.library")
    id("dukaanai.android.hilt")
}

android {
    namespace = "ai.dukaan.core.common"
}

dependencies {
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)
}
