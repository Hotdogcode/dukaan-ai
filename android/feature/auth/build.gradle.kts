plugins {
    id("dukaanai.android.feature")
}

android {
    namespace = "ai.dukaan.feature.auth"
}

dependencies {
    implementation(project(":core:common"))

    testImplementation(project(":core:testing"))
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.mockk)
    testImplementation(libs.turbine)
}
