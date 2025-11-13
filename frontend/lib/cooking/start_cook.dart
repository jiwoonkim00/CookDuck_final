import 'package:flutter/material.dart';
import 'package:cookduck/cooking/chat_cook.dart';

class StartCook extends StatefulWidget {
  const StartCook({super.key});

  @override
  State<StartCook> createState() => _StartCookState();
}

class _StartCookState extends State<StartCook> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Text('JMT 비빔국수'),
            Image(image: AssetImage('assets/logo.png'), width: 40),
          ],
        ),
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
        backgroundColor: Color(0xFFE8EB87),
      ),

      backgroundColor: Color(0xFFE8EB87),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Container(
          height: MediaQuery.of(context).size.height * 0.8,
          decoration: BoxDecoration(
            color: Colors.white.withAlpha(175),
            borderRadius: BorderRadius.circular(35),
          ),
          child: ChatScreen(),
        ),
      ),
    );
  }
}
