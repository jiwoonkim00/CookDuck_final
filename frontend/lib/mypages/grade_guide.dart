import 'package:flutter/material.dart';

class GradeGuide extends StatelessWidget {
  const GradeGuide({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE8EB87),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('등급 안내', style: TextStyle(color: Colors.black)),
        centerTitle: true,
      ),
      body: Center(
        child: Container(
          width: MediaQuery.of(context).size.width * 0.9,
          padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
          decoration: BoxDecoration(
            color: const Color(0xFFF9F9E3),
            borderRadius: BorderRadius.circular(40),
            border: Border.all(color: Color(0xFF1EA7FF), width: 3),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _gradeRow('assets/newbie.png', '초급', null),
              const SizedBox(height: 24),
              _gradeRow('assets/intermediate.png', '중급', '음식 완성 20개 이상'),
              const SizedBox(height: 24),
              _gradeRow('assets/high.png', '고급', '음식 완성 60개 이상'),
              const SizedBox(height: 24),
              _gradeRow('assets/master.png', '마스터', '음식 완성 100개 이상'),
              const SizedBox(height: 36),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFDEDDC),
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(24),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    elevation: 0,
                  ),
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('확인', style: TextStyle(fontSize: 18)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _gradeRow(String imagePath, String grade, String? desc) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Image.asset(imagePath, width: 100, height: 100),
        const SizedBox(width: 32),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(grade, style: const TextStyle(fontSize: 22)),
              if (desc != null) ...[
                const SizedBox(height: 8),
                Text(desc, style: const TextStyle(fontSize: 18)),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
