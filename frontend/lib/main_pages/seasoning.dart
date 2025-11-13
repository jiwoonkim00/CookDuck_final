import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';

class SeasoningButton extends StatefulWidget {
  const SeasoningButton({
    super.key,
    required this.selected,
    this.style,
    required this.onPressed,
    required this.child,
  });

  final bool selected;
  final ButtonStyle? style;
  final VoidCallback? onPressed;
  final Widget child;

  @override
  State<SeasoningButton> createState() => _SeasoningButtonState();
}

class _SeasoningButtonState extends State<SeasoningButton> {
  late final WidgetStatesController statesController;

  @override
  void initState() {
    super.initState();
    statesController = WidgetStatesController(<WidgetState>{
      if (widget.selected) WidgetState.selected,
    });
  }

  @override
  void didUpdateWidget(SeasoningButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selected != oldWidget.selected) {
      statesController.update(WidgetState.selected, widget.selected);
    }
  }

  @override
  Widget build(BuildContext context) {
    return TextButton(
      statesController: statesController,
      style: widget.style,
      onPressed: widget.onPressed,
      child: widget.child,
    );
  }
}

class Seasoning extends StatefulWidget {
  const Seasoning({super.key});

  @override
  State<Seasoning> createState() => _SeasoningState();
}

class _SeasoningState extends State<Seasoning> {
  List<bool> selectedList = List.generate(9, (_) => false);

  @override
  void initState() {
    super.initState();
    _checkSeasoningDone();
  }

  Future<void> _checkSeasoningDone() async {
    final prefs = await SharedPreferences.getInstance();
    final done = prefs.getBool('seasoningDone') ?? false;
    print('조미료 설정 진입: seasoningDone = $done');
    if (done && mounted) {
      print('조미료 설정 완료됨. 홈으로 이동');
      Navigator.pushReplacementNamed(context, '/home');
    }
  }

  static const ButtonStyle style = ButtonStyle(
    foregroundColor: WidgetStateProperty<Color?>.fromMap(<WidgetState, Color>{
      WidgetState.selected: Colors.white,
    }),
    backgroundColor: WidgetStateProperty<Color?>.fromMap(<WidgetState, Color>{
      WidgetState.selected: Colors.indigo,
    }),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: Color(0xFFE8EB87),
        title: const Row(
          children: [
            Image(image: AssetImage('assets/logo.png'), width: 70),
            Text('\t\t\t\t\t 조미료'),
          ],
        ),
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
      ),

      body: Container(
        width: 340,
        height: 400,
        margin: EdgeInsets.all(40),
        padding: EdgeInsets.all(5),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(175),
          borderRadius: BorderRadius.circular(35),
        ),

        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SeasoningButton(
                  selected: selectedList[0],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[0] = !selectedList[0];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🥢', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('간장'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[1],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[1] = !selectedList[1];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🫘', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('된장'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[2],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[2] = !selectedList[2];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🌶️', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('고추장'),
                    ],
                  ),
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SeasoningButton(
                  selected: selectedList[3],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[3] = !selectedList[3];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🧂', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('소금'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[4],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[4] = !selectedList[4];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('⚫', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('후추'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[5],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[5] = !selectedList[5];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🍬', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('설탕'),
                    ],
                  ),
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SeasoningButton(
                  selected: selectedList[6],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[6] = !selectedList[6];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🌶️', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('고춧가루'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[7],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[7] = !selectedList[7];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🍶', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('식초'),
                    ],
                  ),
                ),
                SeasoningButton(
                  selected: selectedList[8],
                  style: style,
                  onPressed: () {
                    setState(() {
                      selectedList[8] = !selectedList[8];
                    });
                  },
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('🥄', style: TextStyle(fontSize: 22)),
                      SizedBox(height: 2),
                      Text('참기름'),
                    ],
                  ),
                ),
              ],
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
              onPressed: () async {
                final prefs = await SharedPreferences.getInstance();
                final userId = prefs.getString('user_id') ?? '';
                final body = {
                  'userId': userId,
                  '간장': selectedList[0],
                  '된장': selectedList[1],
                  '고추장': selectedList[2],
                  '소금': selectedList[3],
                  '후추': selectedList[4],
                  '설탕': selectedList[5],
                  '고춧가루': selectedList[6],
                  '식초': selectedList[7],
                  '참기름': selectedList[8],
                };
                print('selectedList: $selectedList');
                print('body: $body');
                try {
                  final apiService = ApiService();
                  await apiService.post('/user-seasoning-pivot', body);
                  print('서버 응답: 성공');
                  await prefs.setBool('seasoningDone', true);
                  print('조미료 설정 완료: seasoningDone true로 저장');
                  Navigator.pushReplacementNamed(context, '/home');
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('오류 발생: ${e.toString()}')),
                  );
                }
              },
              child: const Text(
                '확인',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
