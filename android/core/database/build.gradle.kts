plugins {
    id("dukaanai.android.library")
    id("dukaanai.android.room")
    id("dukaanai.android.hilt")
}

android {
    namespace = "ai.dukaan.core.database"

    defaultConfig {
        ksp {
            arg("room.schemaLocation", "$projectDir/schemas")
        }
    }
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:model"))

    testImplementation(project(":core:testing"))
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.robolectric)
    testImplementation(libs.androidx.test.ext.junit)
}
