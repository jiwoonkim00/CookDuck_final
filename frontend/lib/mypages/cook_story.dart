import 'package:flutter/material.dart';
import 'package:cookduck/mypages/cook_calendar.dart';

class CookStory extends StatelessWidget {
  const CookStory({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: Color(0xFFE8EB87),
        title: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('MyDuck CookStory'),
            Image(image: AssetImage('assets/logo.png'), width: 40),
          ],
        ),
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
              padding: const EdgeInsets.symmetric(horizontal: 16),
              width: 340,
              decoration: BoxDecoration(
                color: Colors.white.withAlpha(175),
                borderRadius: BorderRadius.circular(25),
              ),
              child: Row(
                children: const [
                  Icon(Icons.search, color: Colors.black),
                  SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: '검색',
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Container(
              margin: EdgeInsets.all(40),
              padding: EdgeInsets.all(5),
              decoration: BoxDecoration(
                color: Colors.white.withAlpha(175),
                borderRadius: BorderRadius.circular(35),
              ),

              child: CookCalendar(),
            ),
          ],
        ),
      ),
    );
  }
}
