plugins {
    `kotlin-dsl`
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidLibrary") {
            id = "dukaanai.android.library"
            implementationClass = "ai.dukaan.buildlogic.AndroidLibraryConventionPlugin"
        }
        register("androidLibraryCompose") {
            id = "dukaanai.android.library.compose"
            implementationClass = "ai.dukaan.buildlogic.AndroidLibraryComposeConventionPlugin"
        }
        register("androidFeature") {
            id = "dukaanai.android.feature"
            implementationClass = "ai.dukaan.buildlogic.AndroidFeatureConventionPlugin"
        }
        register("androidHilt") {
            id = "dukaanai.android.hilt"
            implementationClass = "ai.dukaan.buildlogic.AndroidHiltConventionPlugin"
        }
        register("androidRoom") {
            id = "dukaanai.android.room"
            implementationClass = "ai.dukaan.buildlogic.AndroidRoomConventionPlugin"
        }
        register("jvmLibrary") {
            id = "dukaanai.jvm.library"
            implementationClass = "ai.dukaan.buildlogic.JvmLibraryConventionPlugin"
        }
    }
}
