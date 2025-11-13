Kakao setup for this project

Computed debug key hash (generated on developer machine):

veO37fxDveFt0XVF9yD/QHW886w=

Steps to finish setup (one-time):

1. Open https://developers.kakao.com and sign in.
2. Go to My Application -> Platform -> Android.
3. Add the key hash above to Key Hashes and save.
4. Verify the Package Name (Application ID) matches the project's applicationId:
   - Check `android/app/build.gradle.kts` -> defaultConfig -> applicationId (currently `com.example.cookduck`).
5. Verify the native app key matches the one used in `lib/main.dart` (KakaoSdk.init). It should be the same as the KAKAO_NATIVE_APP_KEY manifest placeholder in `android/app/build.gradle.kts`.
6. Rebuild and run the app:

```powershell
flutter clean
flutter pub get
flutter run -d emulator-5554
```

Notes:
- For release builds, compute the key hash from your release keystore and add that to Kakao too.
- If you need to regenerate the debug key hash, use the included PowerShell script in `tools/compute_kakao_key_hash.ps1`.

If you'd like, I can add the release key hash as well if you provide the keystore information or the build artifacts.