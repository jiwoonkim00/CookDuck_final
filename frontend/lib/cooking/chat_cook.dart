import 'package:flutter/material.dart';

// Simplified chat screen.
// The original file referenced many services (websocket, audio recorder, audio player)
// and had partial/duplicated code that prevented compilation. To make the project
// buildable while preserving a UI for future extension, this file implements a
// minimal self-contained chat screen with a message list and a record toggle
// that simulates recording (no external APIs).

class ChatScreen extends StatefulWidget {
  const ChatScreen({Key? key}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  bool _isRecording = false;
  final List<String> _messages = [];

  void _toggleRecording() {
    setState(() {
      _isRecording = !_isRecording;
      if (_isRecording) {
        _messages.insert(0, '[나] 녹음 시작 (로컬 시뮬레이션)');
      } else {
        _messages.insert(0, '[나] 녹음 중지 (로컬 시뮬레이션)');
      }
    });
  }

  void _sendText(String text) {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.insert(0, '[나] $text');
      _messages.insert(0, '[AI] (답변 없음 - 오프라인 모드)');
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController();
    return Scaffold(
      appBar: AppBar(title: const Text('쿡덕 챗봇')),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? const Center(child: Text('대화를 시작해보세요.'))
                : ListView.builder(
                    reverse: true,
                    itemCount: _messages.length,
                    itemBuilder: (context, idx) => ListTile(title: Text(_messages[idx])),
                  ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(hintText: '메시지를 입력하세요'),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () {
                    _sendText(controller.text);
                    controller.clear();
                  },
                ),
                FloatingActionButton(
                  mini: true,
                  onPressed: _toggleRecording,
                  child: Icon(_isRecording ? Icons.stop : Icons.mic),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
