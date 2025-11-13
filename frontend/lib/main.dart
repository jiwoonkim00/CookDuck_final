import 'package:cookduck/main_pages/cookduck_main.dart';
import 'package:flutter/material.dart';
import 'start_pages/splash_screen.dart';
import 'start_pages/login_screen.dart';
import 'start_pages/signup_screen.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart';
import 'package:provider/provider.dart';
import 'models/user_controller.dart' as user_controller;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('ko_KR', null);
  KakaoSdk.init(
    nativeAppKey: '3fd1159a43e9230ca57d3967d81df028',
    javaScriptAppKey: '13bf02aba237b505958838d1985ec829',
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => user_controller.UserController(),
      child: MaterialApp(
        title: 'Cook Duck',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE8EB87)),
          useMaterial3: true,
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              minimumSize: const Size.fromHeight(50),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => SplashScreen(),
          '/login': (context) => LoginScreen(),
          '/signup': (context) => SignupScreen(),
          '/home': (context) => CookduckMain(),
        },
      ),
    );
  }
}
