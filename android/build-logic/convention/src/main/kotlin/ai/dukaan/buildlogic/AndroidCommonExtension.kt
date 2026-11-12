package ai.dukaan.buildlogic

import com.android.build.api.dsl.CommonExtension
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.getByType

internal val Project.libs: VersionCatalog
    get() = extensions.getByType<VersionCatalogsExtension>().named("libs")

internal fun Project.configureKotlinAndroid(
    commonExtension: CommonExtension<*, *, *, *, *, *>,
) {
    commonExtension.apply {
        compileSdk = DukaanBuildConfig.COMPILE_SDK

        defaultConfig {
            minSdk = DukaanBuildConfig.MIN_SDK
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }

        compileOptions {
            sourceCompatibility = DukaanBuildConfig.JAVA_VERSION
            targetCompatibility = DukaanBuildConfig.JAVA_VERSION
        }

        testOptions {
            unitTests.isIncludeAndroidResources = true
        }
    }
}
