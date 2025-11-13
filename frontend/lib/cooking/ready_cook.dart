import 'package:flutter/material.dart';
import 'package:cookduck/screens/chat_screen.dart';

class Readycook extends StatelessWidget {
  const Readycook({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: Color(0xFFE8EB87),
        title: Center(child: Text('JMT 비빔국수')),
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
      ),
      body: Container(
        width: 340,
        height: 500,
        margin: EdgeInsets.all(40),
        padding: EdgeInsets.all(5),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(175),
          borderRadius: BorderRadius.circular(35),
        ),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Text(
              '필요 재료: \n 소면 (또는 국수) 200g,오이 1/2개, 당근 약간 (선택), 삶은 달걀 1개, 상추, 깻잎 적당량, 김가루 선택, 참깨 약간 \n 레시피:\n 소면 삶기 끓는 물에 소면을 넣고 4~5분 삶은 뒤 찬 비비기 물기 뺀 소면에 양념장을 넣고 잘 비빈다. 야채를 위에 얹고, 삶은 달걀 반쪽과 김가루, 참깨를 뿌려준다. 완성 그릇에 예쁘게 담아내고, 원하면 얼음 동동 띄운 육수나 오이냉국 곁들이면 최고!',
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFFFFEBCE),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 2),
                shape: RoundedRectangleBorder(
                  side: const BorderSide(color: Colors.black12),
                ),
              ),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ChatScreen()),
                );
              },
              child: const Text(
                '시작하기',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
