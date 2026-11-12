pluginManagement {
    includeBuild("build-logic")
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "dukaanai-android"

// Main Application
include(":app")

// Core Foundation Modules
include(":core:common")
include(":core:model")
include(":core:designsystem")
include(":core:ui")
include(":core:navigation")
include(":core:network")
include(":core:database")
include(":core:datastore")
include(":core:domain")
include(":core:data")
include(":core:testing")

// Feature Modules (Placeholders)
include(":feature:auth")
include(":feature:onboarding")
include(":feature:dashboard")
include(":feature:catalogue")
