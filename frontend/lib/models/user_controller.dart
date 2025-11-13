import 'package:flutter/material.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';

class UserController extends ChangeNotifier {
  Future<void> kakaoLogin(BuildContext context) async {
    try {
      OAuthToken token;
      if (await isKakaoTalkInstalled()) {
        token = await UserApi.instance.loginWithKakaoTalk();
      } else {
        token = await UserApi.instance.loginWithKakaoAccount();
      }
      // Get user info
      final user = await UserApi.instance.me();
      final userId = user.id.toString();
      final userName = user.kakaoAccount?.profile?.nickname ?? '';
      final kakaoToken = token.accessToken;

      // 백엔드에 카카오 토큰 전달하여 사용자 등록/로그인 처리
      try {
        final apiService = ApiService();
        final data = await apiService.post(
          '/kakao-login',
          {
            'accessToken': kakaoToken,
          },
          includeAuth: false,
        );
        
        // 백엔드에서 받은 JWT 토큰 저장
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('user_id', data['userId'] ?? userId);
        await prefs.setString('userName', data['name'] ?? userName);
        await prefs.setString('jwt_token', data['token'] ?? '');

        // Show success
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('카카오 로그인 성공: ${data['name'] ?? userName}')),
          );
        }
        notifyListeners();

        // After successful login, navigate to the main screen that contains
        // the bottom navigation so it's visible to the user.
        if (context.mounted) {
          Navigator.pushReplacementNamed(context, '/home');
        }
      } catch (e) {
        debugPrint('Backend kakao login error: $e');
        throw e;
      }
    } catch (e) {
      debugPrint('Kakao login error: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('카카오 로그인 실패: $e')),
        );
      }
    }
  }
}
