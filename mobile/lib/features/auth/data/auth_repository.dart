import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../domain/user_session.dart';

class AuthResponse {
  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final UserSession user;

  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      expiresIn: json['expires_in'] as int,
      user: UserSession.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

class AuthRepository {
  final ApiClient _apiClient;

  AuthRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<AuthResponse> login(String email, String password) async {
    final res = await _apiClient.post('/auth/login', {
      'email': email,
      'password': password,
    });
    return AuthResponse.fromJson(res as Map<String, dynamic>);
  }

  Future<UserSession> getCurrentUser() async {
    final res = await _apiClient.get('/auth/me');
    return UserSession.fromJson(res as Map<String, dynamic>);
  }

  Future<AuthResponse> refreshToken(String refreshToken) async {
    final res = await _apiClient.post('/auth/refresh', {
      'refresh_token': refreshToken,
    });
    return AuthResponse.fromJson(res as Map<String, dynamic>);
  }

  Future<void> logout(String? refreshToken) async {
    try {
      final payload = <String, dynamic>{
        ...?((refreshToken != null) ? {'refresh_token': refreshToken} : null),
      };
      await _apiClient.post('/auth/logout', payload);
    } catch (_) {
      // Ignore network errors on logout
    }
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});
