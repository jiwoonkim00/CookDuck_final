// Flutter 연동 예시 코드
// lib/services/api_service.dart

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:81';
  
  // Spring Boot API 호출 (레시피 추천)
  static Future<Map<String, dynamic>> getRecommendations(List<String> ingredients) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/recommend'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'ingredients': ingredients}),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load recommendations: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('API 호출 실패: $e');
    }
  }
  
  // RAG 기반 추천
  static Future<Map<String, dynamic>> getRagRecommendations(List<String> ingredients) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/recommend/rag'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'ingredients': ingredients}),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load RAG recommendations: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('RAG API 호출 실패: $e');
    }
  }
  
  // 시스템 상태 확인
  static Future<Map<String, dynamic>> getSystemStatus() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/system/status'),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load system status: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('시스템 상태 확인 실패: $e');
    }
  }
  
  // 성능 측정
  static Future<Map<String, dynamic>> measurePerformance(List<String> ingredients) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/recommend/performance'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'ingredients': ingredients}),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to measure performance: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('성능 측정 실패: $e');
    }
  }
  
  // 헬스 체크
  static Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/health'),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('헬스 체크 실패: $e');
    }
  }
}

// WebSocket 서비스 (음성 채팅)
class WebSocketService {
  late WebSocketChannel channel;
  
  void connect() {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:81/api/fastapi/ws/chat'),
    );
  }
  
  void sendAudio(List<int> audioData) {
    channel.sink.add(audioData);
  }
  
  Stream<dynamic> get stream => channel.stream;
  
  void disconnect() {
    channel.sink.close();
  }
}

// 사용 예시
class RecipeRecommendationWidget extends StatefulWidget {
  @override
  _RecipeRecommendationWidgetState createState() => _RecipeRecommendationWidgetState();
}

class _RecipeRecommendationWidgetState extends State<RecipeRecommendationWidget> {
  List<String> ingredients = ['김치', '계란', '고추장'];
  Map<String, dynamic>? recommendations;
  bool isLoading = false;
  
  @override
  void initState() {
    super.initState();
    loadRecommendations();
  }
  
  Future<void> loadRecommendations() async {
    setState(() {
      isLoading = true;
    });
    
    try {
      // FAISS 기반 추천
      final faissResult = await ApiService.getRecommendations(ingredients);
      
      // RAG 기반 추천
      final ragResult = await ApiService.getRagRecommendations(ingredients);
      
      setState(() {
        recommendations = {
          'faiss': faissResult,
          'rag': ragResult,
        };
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('추천 로딩 실패: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('레시피 추천')),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : recommendations != null
              ? ListView(
                  children: [
                    Card(
                      child: ListTile(
                        title: Text('FAISS 추천'),
                        subtitle: Text('${recommendations!['faiss'].length}개 결과'),
                      ),
                    ),
                    Card(
                      child: ListTile(
                        title: Text('RAG 추천'),
                        subtitle: Text(recommendations!['rag']['rag_result']['title']),
                      ),
                    ),
                  ],
                )
              : Center(child: Text('추천 결과가 없습니다.')),
    );
  }
}
