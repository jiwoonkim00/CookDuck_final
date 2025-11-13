# Kakao SDK keep (패키지 버전에 따라 조정)
-keep class com.kakao.** { *; }
-dontwarn com.kakao.**

# Kotlin/Coroutines 등 일반 권장
-keep class kotlinx.** { *; }
-dontwarn kotlinx.**

# Flutter 관련
-keep class io.flutter.** { *; }
-dontwarn io.flutter.**

# JSON 직렬화
-keep class com.google.gson.** { *; }
-dontwarn com.google.gson.**


