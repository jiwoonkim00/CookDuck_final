import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/services/api_service.dart' show ApiService;

class ChatScreen extends StatefulWidget {
  final Recipe? recipe;

  const ChatScreen({super.key, this.recipe});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  WebSocketChannel? _channel;
  final AudioRecorder _audioRecorder = AudioRecorder();
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isRecording = false;
  bool _isConnected = false;
  String? _currentAudioPath;
  bool _isPlayingAudio = false; // 오디오 재생 중 플래그
  List<int> _audioBuffer = []; // TTS 스트리밍 버퍼

  void _safeSetState(VoidCallback fn) {
    if (mounted) {
      setState(fn);
    } else {
      fn();
    }
  }

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  Future<void> _connectWebSocket() async {
    int retryCount = 0;
    const maxRetries = 3;
    
    while (retryCount < maxRetries) {
      try {
        // 레시피가 있으면 레시피 기반 챗봇, 없으면 일반 챗봇
        final baseUrl = ApiService.baseUrl.replaceFirst('http://', 'ws://');
        final wsUrl = widget.recipe != null
            ? '$baseUrl/gateapi/ws/recipe-chat'
            : '$baseUrl/gateapi/ws/chat';

        print('🔌 WebSocket 연결 시도 ${retryCount + 1}/$maxRetries: $wsUrl');
        
        // WebSocket 연결 시도
        bool connectionFailed = false;
        String? connectionError;
        
        try {
          _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
        } catch (e) {
          // 동기 연결 실패
          throw Exception('WebSocket 연결 실패: $e');
        }
        
        // 연결 에러를 감지하기 위한 Completer
        final connectionCompleter = Completer<bool>();
        bool connectionConfirmed = false;
        
        // 메시지 수신 리스너 설정 (연결 확인과 메시지 처리 모두 수행)
        _channel!.stream.listen(
          (message) {
            // 연결 확인 (첫 메시지 수신 시)
            if (!connectionConfirmed) {
              connectionConfirmed = true;
              if (!connectionCompleter.isCompleted) {
                connectionCompleter.complete(true);
              }
              _safeSetState(() => _isConnected = true);
              print('✅ WebSocket 연결 확인됨');
            }
            
            // 메시지 처리
            if (message is String) {
              try {
                final data = json.decode(message);
                _handleWebSocketMessage(data);
              } catch (e) {
                // 텍스트 메시지인 경우
                _addMessage('봇', message, isUser: false);
              }
            } else if (message is List<int>) {
              // 오디오 데이터 수신 (TTS 스트리밍 청크)
              // 버퍼에 추가하고, TTS_STREAM_END 이벤트를 기다림
              _audioBuffer.addAll(message);
              print('🎵 오디오 청크 수신: ${message.length} bytes (버퍼: ${_audioBuffer.length} bytes)');
            }
          },
          onError: (error) {
            // 연결 확인 전 에러인 경우
            if (!connectionCompleter.isCompleted) {
              connectionFailed = true;
              connectionError = error.toString();
              connectionCompleter.complete(false);
              print('❌ WebSocket 연결 에러 감지: $error');
            } else {
              // 연결 후 에러
              print('WebSocket 에러: $error');
              _safeSetState(() => _isConnected = false);
              _addMessage('시스템', '연결 오류가 발생했습니다.', isUser: false);
              if (_isRecording) {
                _audioRecorder.stop();
                _safeSetState(() => _isRecording = false);
              }
            }
          },
          onDone: () {
            print('WebSocket 연결 종료');
            _safeSetState(() => _isConnected = false);
            if (_isRecording) {
              _audioRecorder.stop();
              _safeSetState(() => _isRecording = false);
            }
          },
          cancelOnError: false,
        );
        
        // 연결이 실제로 완료될 때까지 대기 (최대 1.5초)
        try {
          final connected = await connectionCompleter.future.timeout(
            const Duration(milliseconds: 1500),
            onTimeout: () {
              // 타임아웃 = 연결 성공 (에러가 발생하지 않음)
              if (!connectionConfirmed) {
                _safeSetState(() => _isConnected = true);
                print('✅ WebSocket 연결 성공 (타임아웃)');
              }
              return true;
            },
          );
          
          if (!connected || connectionFailed) {
            throw Exception('WebSocket 연결 실패: $connectionError');
          }
        } catch (e) {
          if (connectionFailed) {
            throw Exception('WebSocket 연결 실패: $connectionError');
          }
          // 타임아웃이 아닌 다른 에러는 무시 (연결 성공으로 간주)
        }

        // 레시피 데이터 전송 (레시피 기반 챗봇인 경우)
        if (widget.recipe != null) {
          final recipeData = {
            'selected_recipe': {
              'id': widget.recipe!.id,
              'title': widget.recipe!.title,
              'content': widget.recipe!.content,
              'description': widget.recipe!.description,
              'ingredients': widget.recipe!.ingredients,
              'servings': widget.recipe!.servings,
              'cuisine': widget.recipe!.cuisine,
            }
          };
          print('📤 레시피 데이터 전송: ${widget.recipe!.title}');
          _channel!.sink.add(json.encode(recipeData));
        }

        // 연결 성공 (자동 녹음 제거 - 수동 녹음만 사용)
        return; // 연결 성공 시 함수 종료
      } catch (e) {
        retryCount++;
        print('❌ WebSocket 연결 실패 (시도 $retryCount/$maxRetries): $e');
        
        if (retryCount >= maxRetries) {
          print('❌ WebSocket 연결 최대 재시도 횟수 초과');
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('챗봇 연결 실패: 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.'),
                duration: const Duration(seconds: 5),
              ),
            );
          }
          return;
        }
        
        // 재시도 전 대기
        await Future.delayed(Duration(seconds: retryCount * 2));
        print('🔄 WebSocket 재연결 시도 중...');
      }
    }
  }

  void _handleWebSocketMessage(Map<String, dynamic> data) {
    final type = data['type'];
    final messageData = data['data'];

    switch (type) {
      case 'bot_text':
        _addMessage('쿡덕', messageData, isUser: false);
        break;
      case 'user_text':
        _addMessage('나', messageData, isUser: true);
        break;
      case 'event':
        if (messageData == 'TTS_STREAM_END') {
          print('TTS 스트리밍 완료');
          // 버퍼에 쌓인 오디오가 있으면 재생
          if (_audioBuffer.isNotEmpty) {
            final audioToPlay = List<int>.from(_audioBuffer);
            _audioBuffer.clear();
            _playAudioBytes(audioToPlay);
          }
        }
        break;
    }
  }

  void _addMessage(String sender, String text, {required bool isUser}) {
    if (!mounted) return;
    _safeSetState(() {
      _messages.add({
        'sender': sender,
        'text': text,
        'isUser': isUser,
        'timestamp': DateTime.now(),
      });
    });
    _scrollToBottom();
  }

  Future<void> _playAudioBytes(List<int> audioBytes) async {
    // 이미 재생 중이면 스킵 (중복 재생 방지)
    if (_isPlayingAudio) {
      print('오디오 재생 중이므로 스킵');
      return;
    }
    
    try {
      _isPlayingAudio = true;
      
      // 챗봇이 말하는 동안 녹음 중지 (수동 녹음인 경우)
      if (_isRecording) {
        print('🎵 챗봇 말하는 중 - 녹음 일시 중지');
        await _audioRecorder.stop();
        _safeSetState(() => _isRecording = false);
      }
      
      final tempDir = await getTemporaryDirectory();
      final audioFile = File('${tempDir.path}/temp_audio_${DateTime.now().millisecondsSinceEpoch}.wav');
      await audioFile.writeAsBytes(audioBytes);
      
      print('🎵 오디오 파일 생성: ${audioFile.path}, 크기: ${audioBytes.length} bytes');
      
      // 재생 시작
      await _audioPlayer.play(DeviceFileSource(audioFile.path));
      print('🎵 오디오 재생 시작');
      
      // 재생 완료 대기 (최대 10초)
      try {
        await _audioPlayer.onPlayerComplete.first.timeout(
          const Duration(seconds: 10),
          onTimeout: () {
            print('오디오 재생 타임아웃');
          },
        );
        print('🎵 오디오 재생 완료');
      } catch (e) {
        print('오디오 재생 완료 대기 중 에러: $e');
      }
      
      // 재생 완료 후 파일 삭제
      try {
        if (await audioFile.exists()) {
          await audioFile.delete();
          print('🎵 오디오 파일 삭제 완료');
        }
      } catch (deleteError) {
        // 파일 삭제 실패는 무시 (이미 삭제되었을 수 있음)
        print('파일 삭제 실패 (무시): $deleteError');
      }
    } catch (e) {
      print('오디오 재생 실패: $e');
    } finally {
      _isPlayingAudio = false;
      // 재생 완료 (수동 녹음은 사용자가 직접 시작)
    }
  }

  Future<void> _startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        final tempDir = await getTemporaryDirectory();
        _currentAudioPath = '${tempDir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.wav';
        
        await _audioRecorder.start(
          const RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          ),
          path: _currentAudioPath!,
        );
        
        _safeSetState(() => _isRecording = true);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('마이크 권한이 필요합니다.')),
          );
        }
      }
    } catch (e) {
      print('녹음 시작 실패: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('녹음 시작 실패: $e')),
        );
      }
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await _audioRecorder.stop();
      _safeSetState(() => _isRecording = false);

      // 챗봇이 말하는 중이면 전송하지 않음
      if (_isPlayingAudio) {
        print('🎤 챗봇이 말하는 중이므로 오디오 전송 스킵');
        if (path != null) {
          File(path).delete();
        }
        return;
      }

      if (path != null && _channel != null && _isConnected) {
        final audioFile = File(path);
        final audioBytes = await audioFile.readAsBytes();
        
        print('🎤 오디오 파일 크기: ${audioBytes.length} bytes');
        print('🎤 WebSocket 연결 상태: $_isConnected');
        
        // WebSocket으로 오디오 전송
        try {
          _channel!.sink.add(audioBytes);
          print('✅ 오디오 데이터 전송 완료');
        } catch (e) {
          print('❌ 오디오 전송 실패: $e');
          if (mounted) {
            _addMessage('시스템', '음성 전송 실패: $e', isUser: false);
          }
        }
        
        // 임시 파일 삭제
        audioFile.delete();
      } else if (path != null) {
        print('⚠️ 오디오 파일이 있지만 전송 조건 불만족: path=$path, channel=${_channel != null}, connected=$_isConnected');
        File(path).delete();
      } else {
        print('⚠️ 녹음 파일 경로가 null입니다');
      }
    } catch (e) {
      print('녹음 중지 실패: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('녹음 중지 실패: $e')),
        );
      }
    }
  }


  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    if (_isRecording) {
      _audioRecorder.stop();
      _isRecording = false;
    }
    _audioRecorder.dispose();
    _audioPlayer.dispose();
    _channel?.sink.close();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.recipe != null ? '${widget.recipe!.title} 챗봇' : '쿡덕 AI 챗봇'),
        backgroundColor: const Color(0xFFE8EB87),
      ),
      backgroundColor: const Color(0xFFE8EB87),
      body: Column(
        children: [
          if (!_isConnected)
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.orange.shade200,
              child: const Row(
                children: [
                  Icon(Icons.warning, color: Colors.orange),
                  SizedBox(width: 8),
                  Text('연결 중...', style: TextStyle(fontSize: 14)),
                ],
              ),
            ),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message['isUser'] as bool;
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 5, horizontal: 8),
                    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 18),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blueAccent : Colors.white,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (!isUser)
                          Text(
                            message['sender'] as String,
                            style: TextStyle(
                              fontSize: 12,
                              color: isUser ? Colors.white70 : Colors.black54,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        const SizedBox(height: 4),
                        Text(
                          message['text'] as String,
                          style: TextStyle(
                            fontSize: 16,
                            color: isUser ? Colors.white : Colors.black87,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          if (!_isConnected) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('챗봇에 연결되지 않았습니다.')),
              );
            }
            return;
          }
          
          // 수동 녹음 시작/중지
          if (_isRecording) {
            _stopRecording();
          } else {
            // 챗봇이 말하는 중이면 녹음 시작하지 않음
            if (_isPlayingAudio) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('챗봇이 말하는 중입니다. 잠시 후 다시 시도해주세요.')),
                );
              }
              return;
            }
            _startRecording();
          }
        },
        backgroundColor: _isRecording 
            ? Colors.red 
            : (_isConnected ? Colors.blue : Colors.grey),
        child: Icon(_isRecording ? Icons.stop : Icons.mic),
      ),
    );
  }
}
