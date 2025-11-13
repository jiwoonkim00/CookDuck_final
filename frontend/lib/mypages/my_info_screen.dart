import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';
import 'package:cookduck/mypages/change_password_screen.dart';

class MyInfoScreen extends StatefulWidget {
  const MyInfoScreen({super.key});

  @override
  State<MyInfoScreen> createState() => _MyInfoScreenState();
}

class _MyInfoScreenState extends State<MyInfoScreen> {
  String? userName;
  String? userEmail;
  String? userGrade;
  String? userId;
  bool isLoading = true;
  String? errorMsg;

  @override
  void initState() {
    super.initState();
    _fetchUserInfo();
  }

  Future<void> _fetchUserInfo() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final prefsUserId = prefs.getString('user_id');
      print('[내정보] SharedPreferences user_id: ${prefsUserId ?? 'null'}');
      if (prefsUserId == null || prefsUserId.isEmpty) {
        setState(() {
          errorMsg = '로그인 정보가 없습니다.';
          isLoading = false;
        });
        print('[내정보] user_id 없음, 로그인 필요');
        return;
      }
      final apiService = ApiService();
      final data = await apiService.get('/user/$prefsUserId');
      print('[내정보] 파싱된 데이터: $data');
      setState(() {
        userName = data['name'] ?? '';
        userEmail = data['email'] ?? '';
        userGrade = data['grade'] ?? '';
        userId = data['userId'] ?? '';
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMsg = '에러: $e';
        isLoading = false;
      });
      print('[내정보] 예외 발생: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE8EB87),
        elevation: 0,
        title: const Text('내 정보', style: TextStyle(color: Colors.black)),
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Center(
        child:
            isLoading
                ? const CircularProgressIndicator()
                : errorMsg != null
                ? Text(errorMsg!, style: const TextStyle(color: Colors.red))
                : Container(
                  width: 320,
                  padding: const EdgeInsets.symmetric(
                    vertical: 32,
                    horizontal: 20,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF9F9E3),
                    borderRadius: BorderRadius.circular(32),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '이름',
                        style: TextStyle(fontSize: 16, color: Colors.black54),
                      ),
                      const SizedBox(height: 4),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Text(
                            userName ?? '',
                            style: const TextStyle(fontSize: 18),
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      const Text(
                        '아이디',
                        style: TextStyle(fontSize: 16, color: Colors.black54),
                      ),
                      const SizedBox(height: 4),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Text(
                            userId ?? '',
                            style: const TextStyle(fontSize: 18),
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      const Text(
                        '이메일',
                        style: TextStyle(fontSize: 16, color: Colors.black54),
                      ),
                      const SizedBox(height: 4),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Text(
                            userEmail ?? '',
                            style: const TextStyle(fontSize: 18),
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      const Text(
                        '등급',
                        style: TextStyle(fontSize: 16, color: Colors.black54),
                      ),
                      const SizedBox(height: 4),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Text(
                            userGrade ?? '',
                            style: const TextStyle(fontSize: 18),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF1EA7FF),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20),
                            ),
                          ),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder:
                                    (context) => const ChangePasswordScreen(),
                              ),
                            );
                          },
                          child: const Text(
                            '비밀번호 변경',
                            style: TextStyle(fontSize: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
      ),
    );
  }
}
