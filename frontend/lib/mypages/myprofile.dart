import 'package:cookduck/mypages/bookmark.dart';
import 'package:cookduck/mypages/cook_story.dart';
import 'package:cookduck/mypages/delete_id.dart';
import 'package:flutter/material.dart';
import 'package:cookduck/main_pages/myrefrig.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';
import 'package:cookduck/mypages/grade_guide.dart';
import 'package:cookduck/mypages/my_info_screen.dart';

class Myprofile extends StatefulWidget {
  const Myprofile({super.key});

  @override
  State<Myprofile> createState() => _MyprofileState();
}

class _MyprofileState extends State<Myprofile> {
  String? userName;
  String? userGrade;

  @override
  void initState() {
    super.initState();
    _loadUserName();
    _fetchUserGrade();
  }

  Future<void> _loadUserName() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      userName = prefs.getString('userName') ?? '';
    });
  }

  Future<void> _fetchUserGrade() async {
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id');
    if (userId == null || userId.isEmpty) return;
    try {
      final apiService = ApiService();
      final data = await apiService.get('/user-grade/$userId');
      final grade = data['userGrade'] ?? '';
      setState(() {
        userGrade = grade;
      });
    } catch (e) {
      setState(() {
        userGrade = '에러';
      });
    }
  }

  String _getGradeImage(String? grade) {
    final g = grade?.trim();
    switch (g) {
      case '초보':
      case 'newbie':
        return 'assets/newbie.png';
      case '중급':
      case 'intermediate':
        return 'assets/intermediate.png';
      case '고급':
      case 'high':
        return 'assets/high.png';
      case '마스터':
      case 'master':
        return 'assets/master.png';
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: Color(0xFFE8EB87),
        title: Center(child: Text('마이 페이지')),
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
      ),

      body: SingleChildScrollView(
        child: Column(
          children: [
            Container(
              margin: EdgeInsets.only(bottom: 25),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 150,
                    height: 200,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Container(
                          alignment: Alignment.center,
                          width: 150,
                          padding: EdgeInsets.symmetric(vertical: 8),
                          color: Colors.white.withAlpha(195),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                '이름',
                                style: TextStyle(
                                  color: Colors.black,
                                  fontSize: 22,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                userName ?? '',
                                style: TextStyle(
                                  color: Colors.black,
                                  fontSize: 18,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          margin: EdgeInsets.only(top: 20),
                          alignment: Alignment.center,
                          width: 150,
                          height: 50,
                          color: Colors.white.withAlpha(195),
                          child: GestureDetector(
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const GradeGuide(),
                                ),
                              );
                            },
                            child: Text(
                              '등급 설명 보기',
                              style: TextStyle(
                                color: Colors.black,
                                fontSize: 22,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    width: 150,
                    height: 200,
                    decoration: BoxDecoration(
                      color: Colors.white.withAlpha(195),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const GradeGuide(),
                          ),
                        );
                      },
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (userGrade != null &&
                              _getGradeImage(userGrade).isNotEmpty)
                            Image.asset(
                              _getGradeImage(userGrade),
                              width: 64,
                              height: 64,
                            ),
                          if (userGrade != null &&
                              _getGradeImage(userGrade).isEmpty)
                            Icon(Icons.person, size: 64),
                          SizedBox(height: 8),
                          Text(
                            userGrade ?? '',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Container(
              width: 200,
              height: 330,
              margin: EdgeInsets.only(top: 15),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const MyInfoScreen(),
                        ),
                      );
                    },
                    child: Text(
                      '내 정보 확인',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => Bookmark()),
                      );
                    },
                    child: Text(
                      '북마크 확인',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => CookStory()),
                      );
                    },
                    child: Text(
                      '레시피 기록 확인',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => Myrefrig()),
                      );
                    },
                    child: Text(
                      '내 냉장고 확인',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () async {
                      final prefs = await SharedPreferences.getInstance();
                      final seasoningDone =
                          prefs.getBool('seasoningDone') ?? false;
                      await prefs.clear();
                      if (seasoningDone) {
                        await prefs.setBool('seasoningDone', true);
                      }
                      if (context.mounted) {
                        Navigator.of(
                          context,
                        ).pushNamedAndRemoveUntil('/login', (route) => false);
                      }
                    },
                    child: Text(
                      '로그아웃',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => DeleteId()),
                      );
                    },
                    child: Text(
                      '회원탈퇴',
                      style: TextStyle(
                        color: const Color.fromARGB(255, 255, 0, 0),
                        fontSize: 22,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
