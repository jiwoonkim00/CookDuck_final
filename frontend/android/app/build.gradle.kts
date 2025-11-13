plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")        // ✅ 최신 ID
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.cookduck"
    compileSdk = 35  // Android SDK 35로 업데이트
    ndkVersion = "27.0.12077973"

    compileOptions {
        // ✅ Java 17 사용
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17" // ✅ Java 17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.example.cookduck"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = 21  // 최소 SDK 버전
        targetSdk = 35  // 타겟 SDK 버전
        versionCode = flutter.versionCode
        versionName = flutter.versionName

        // ✅ 카카오 네이티브 앱 키를 매니페스트로 전달
        // 실제 배포에서는 환경변수/gradle.properties로 주입 권장
        manifestPlaceholders["kakaoAppKey"] = "3fd1159a43e9230ca57d3967d81df028"  // 네이티브 앱 키
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro" // ✅ 카카오 keep 예시 추가
            )
        }
        debug {
            // 디버그는 난독화 X
            isMinifyEnabled = false
        }
    }
}

flutter {
    source = "../.."
}
