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

  /// Hook for retrieving active Bearer access token
  String? Function()? getAccessToken;

  /// Hook for performing async token refresh on 401 response
  Future<bool> Function()? onRefreshToken;

  /// In-flight refresh future to coalesce concurrent 401s into a single refresh flight
  Future<bool>? _refreshFuture;

  final http.Client _client = http.Client();
  static const Duration timeout = Duration(seconds: 4);

  Map<String, String> _buildHeaders({Map<String, String>? extra}) {
    final headers = <String, String>{
      'Accept': 'application/json',
      ...?extra,
    };
    final token = getAccessToken?.call();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  HttpException _parseError(int statusCode, String body, String fallback) {
    try {
      final json = jsonDecode(body);
      if (json is Map<String, dynamic>) {
        final detail = json['detail'] as String?;
        final title = json['title'] as String?;
        if (detail != null) {
          return HttpException(detail, statusCode: statusCode, title: title);
        }
      }
    } catch (_) {}
    return HttpException(fallback, statusCode: statusCode);
  }

  /// Perform token refresh coalesced into a single flight.
  /// Concurrent 401 calls await the same single future to avoid race conditions.
  Future<bool> _refreshAccessToken() async {
    if (onRefreshToken == null) return false;
    if (_refreshFuture != null) {
      return _refreshFuture!;
    }

    final future = onRefreshToken!();
    _refreshFuture = future;
    try {
      return await future;
    } finally {
      _refreshFuture = null;
    }
  }

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
    var response = await _client
        .get(uri, headers: _buildHeaders())
        .timeout(timeout);

    // Automatic token refresh attempt on 401 (except on /auth routes)
    if (response.statusCode == 401 && !path.startsWith('/auth') && onRefreshToken != null) {
      final refreshed = await _refreshAccessToken();
      if (refreshed) {
        response = await _client
            .get(uri, headers: _buildHeaders())
            .timeout(timeout);
      }
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw _parseError(
      response.statusCode,
      response.body,
      'GET $path failed: ${response.statusCode} ${response.body}',
    );
  }

  /// Perform a POST request.
  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$_baseUrl$path');
    final reqHeaders = _buildHeaders(extra: {'Content-Type': 'application/json'});

    var response = await _client
        .post(uri, headers: reqHeaders, body: jsonEncode(body))
        .timeout(timeout);

    // Automatic token refresh attempt on 401 (except on /auth routes)
    if (response.statusCode == 401 && !path.startsWith('/auth') && onRefreshToken != null) {
      final refreshed = await _refreshAccessToken();
      if (refreshed) {
        final retryHeaders = _buildHeaders(extra: {'Content-Type': 'application/json'});
        response = await _client
            .post(uri, headers: retryHeaders, body: jsonEncode(body))
            .timeout(timeout);
      }
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw _parseError(
      response.statusCode,
      response.body,
      'POST $path failed: ${response.statusCode} ${response.body}',
    );
  }

  /// Perform a PATCH request.
  Future<dynamic> patch(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$_baseUrl$path');
    final reqHeaders = _buildHeaders(extra: {'Content-Type': 'application/json'});

    var response = await _client
        .patch(uri, headers: reqHeaders, body: jsonEncode(body))
        .timeout(timeout);

    if (response.statusCode == 401 && !path.startsWith('/auth') && onRefreshToken != null) {
      final refreshed = await _refreshAccessToken();
      if (refreshed) {
        final retryHeaders = _buildHeaders(extra: {'Content-Type': 'application/json'});
        response = await _client
            .patch(uri, headers: retryHeaders, body: jsonEncode(body))
            .timeout(timeout);
      }
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw _parseError(
      response.statusCode,
      response.body,
      'PATCH $path failed: ${response.statusCode} ${response.body}',
    );
  }
}

class HttpException implements Exception {
  final String message;
  final int? statusCode;
  final String? title;

  HttpException(this.message, {this.statusCode, this.title});

  @override
  String toString() => message;
}
