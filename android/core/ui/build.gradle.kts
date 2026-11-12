plugins {
    id("dukaanai.android.library.compose")
}

android {
    namespace = "ai.dukaan.core.ui"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:designsystem"))
}
