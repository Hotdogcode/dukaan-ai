plugins {
    id("dukaanai.android.feature")
}

android {
    namespace = "ai.dukaan.feature.dashboard"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:domain"))
}
