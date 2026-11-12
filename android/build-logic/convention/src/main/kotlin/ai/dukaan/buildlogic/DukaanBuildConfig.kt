package ai.dukaan.buildlogic

import org.gradle.api.JavaVersion

object DukaanBuildConfig {
    const val COMPILE_SDK = 35
    const val MIN_SDK = 26
    const val TARGET_SDK = 35
    val JAVA_VERSION = JavaVersion.VERSION_21
    const val JVM_TARGET = "21"
}
