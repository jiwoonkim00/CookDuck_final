import 'package:flutter/material.dart';

class ApproveDialogContent extends StatelessWidget {
  const ApproveDialogContent({super.key});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(230),
          borderRadius: BorderRadius.circular(16),
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Image.asset('assets/logo.png', width: 50),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'COOKDUCK에 사용되는 접근권한 안내',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                '필수 접근권한',
                style: TextStyle(fontSize: 14, color: Colors.red),
              ),
              const SizedBox(height: 8),
              const Text(
                'COOKDUCK은 동의가 필요한 필수 접근권한은\n사용하지 않습니다.',
                style: TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 16),
              const Text(
                '선택 접근권한',
                style: TextStyle(fontSize: 14, color: Colors.blue),
              ),
              const SizedBox(height: 8),
              const Text(
                '선택 접근권한은 동의하지 않아도 서비스 이용이\n가능하나, 해당 권한이 필요한 기능은 제한될 수\n있습니다.',
                style: TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 20),
              Align(
                alignment: Alignment.centerRight,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).pop(true); // 팝업 닫기
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFFEBCE),
                    foregroundColor: Colors.black,
                  ),
                  child: const Text('확인'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
