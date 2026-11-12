# ==============================================================================
# DukaanAI ProGuard & R8 Optimization Baseline Rules
# ==============================================================================

# Kotlin Serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.SerializationKt
-keepclassmembers class * {
    *** Companion;
}
-keepclasseswithmembers class * {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit
-dontnote retrofit2.Platform
-dontwarn retrofit2.Platform$Java8
-keepattributes Signature, Exceptions

# Room
-keepclassmembers class * extends androidx.room.RoomDatabase {
    static <fields>;
}

# Coroutines
-dontwarn kotlinx.coroutines.**

# DukaanAI Domain Models
-keep class ai.dukaan.core.model.** { *; }
-keep class ai.dukaan.core.navigation.** { *; }
