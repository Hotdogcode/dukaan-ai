plugins {
    id("dukaanai.android.library")
    id("dukaanai.android.hilt")
}

android {
    namespace = "ai.dukaan.core.datastore"
}

dependencies {
    implementation(project(":core:common"))
    implementation(project(":core:model"))

    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.datastore.core)
}
