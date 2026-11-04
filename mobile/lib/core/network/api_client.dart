import 'dart:async';
import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  /// Resolve the default base URL based on platform.
  /// On Android emulator, localhost is 10.0.2.2.
  /// On desktop, iOS simulator, or web, localhost is 127.0.0.1.
  static String get defaultBaseUrl {
    const fromDefine = String.fromEnvironment('API_BASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;

    if (!kIsWeb) {
      try {
        if (Platform.isAndroid) {
          return 'http://10.0.2.2:8000/api/v1';
        }
      } catch (_) {
        // Fall through on non-standard platforms
      }
    }
    return 'http://127.0.0.1:8000/api/v1';
  }

  String _baseUrl = defaultBaseUrl;
  String get baseUrl => _baseUrl;

  void setBaseUrl(String url) {
    _baseUrl = url;
  }

  final http.Client _client = http.Client();
  static const Duration timeout = Duration(seconds: 4);

  /// Check whether the backend is reachable and healthy.
  Future<bool> checkBackendHealth() async {
    try {
      final uri = Uri.parse('$_baseUrl/readiness');
      final response = await _client.get(uri).timeout(const Duration(seconds: 2));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Perform a GET request.
  Future<dynamic> get(String path) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _client.get(uri, headers: {
      'Accept': 'application/json',
    }).timeout(timeout);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw HttpException('GET $path failed: ${response.statusCode} ${response.body}');
  }

  /// Perform a POST request.
  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _client
        .post(
          uri,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: jsonEncode(body),
        )
        .timeout(timeout);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw HttpException('POST $path failed: ${response.statusCode} ${response.body}');
  }

  /// Perform a PATCH request.
  Future<dynamic> patch(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _client
        .patch(
          uri,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: jsonEncode(body),
        )
        .timeout(timeout);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw HttpException('PATCH $path failed: ${response.statusCode} ${response.body}');
  }
}

class HttpException implements Exception {
  final String message;
  HttpException(this.message);
  @override
  String toString() => message;
}
