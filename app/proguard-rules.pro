# Retrofit / OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keepattributes Signature
-keepattributes *Annotation*
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}

# Kotlinx Serialization
-keepattributes InnerClasses
-keepclassmembers class kotlinx.serialization.json.** { *; }
-keepclasseswithmembers class * {
    kotlinx.serialization.KSerializer serializer(...);
}

# Room
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**

# Hilt
-dontwarn com.google.errorprone.annotations.**

# Kotlinx Serialization — keep API DTOs used by Retrofit/WebSocket
-keep @kotlinx.serialization.Serializable class org.jaltediye.cereqon.data.remote.dto.** { *; }
-keepclassmembers class org.jaltediye.cereqon.data.remote.dto.** {
    <fields>;
}
