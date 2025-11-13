import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // 서버 URL 설정 (Nginx를 통한 통합 접근)
  static const String baseUrl = 'http://192.168.0.35:81/api';
  
  // JWT 토큰 가져오기
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }

  // 기본 헤더 (인증 포함)
  Future<Map<String, String>> _getHeaders({bool includeAuth = true}) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    
    if (includeAuth) {
      final token = await _getToken();
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    
    return headers;
  }

  // GET 요청
  Future<dynamic> get(
    String endpoint, {
    bool includeAuth = true,
    Map<String, String>? queryParameters,
  }) async {
    try {
      Uri uri = Uri.parse('$baseUrl$endpoint');

      if (queryParameters != null && queryParameters.isNotEmpty) {
        final updatedParams = Map<String, String>.from(uri.queryParameters)
          ..addAll(queryParameters);
        uri = uri.replace(queryParameters: updatedParams);
      }

      final response = await http.get(uri, headers: await _getHeaders(includeAuth: includeAuth));
      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to make GET request: $e');
    }
  }

  // POST 요청
  Future<dynamic> post(String endpoint, Map<String, dynamic> data, {bool includeAuth = true}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$endpoint'),
        headers: await _getHeaders(includeAuth: includeAuth),
        body: json.encode(data),
      );
      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to make POST request: $e');
    }
  }

  // PUT 요청
  Future<dynamic> put(String endpoint, Map<String, dynamic> data, {bool includeAuth = true}) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl$endpoint'),
        headers: await _getHeaders(includeAuth: includeAuth),
        body: json.encode(data),
      );
      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to make PUT request: $e');
    }
  }

  // DELETE 요청
  Future<dynamic> delete(String endpoint, {bool includeAuth = true}) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl$endpoint'),
        headers: await _getHeaders(includeAuth: includeAuth),
      );
      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to make DELETE request: $e');
    }
  }

  // Multipart POST 요청 (파일 업로드용)
  Future<dynamic> postMultipart(
    String endpoint,
    String fileField,
    String filePath, {
    Map<String, String>? fields,
    bool includeAuth = true,
  }) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl$endpoint'),
      );

      // 파일 추가
      request.files.add(
        await http.MultipartFile.fromPath(fileField, filePath),
      );

      // 추가 필드 추가
      if (fields != null) {
        request.fields.addAll(fields);
      }

      // 인증 헤더 추가
      if (includeAuth) {
        final token = await _getToken();
        if (token != null && token.isNotEmpty) {
          request.headers['Authorization'] = 'Bearer $token';
        }
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return _handleResponse(response);
    } catch (e) {
      throw Exception('Failed to make multipart POST request: $e');
    }
  }

  // 응답 처리
  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return null;
      }
      try {
        return json.decode(response.body);
      } catch (e) {
        return response.body;
      }
    } else {
      throw Exception(
        'API request failed with status code: ${response.statusCode} - ${response.body}',
      );
    }
  }
}
