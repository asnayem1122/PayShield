import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../core/role/demo_role.dart';
import '../data/auth_repository.dart';
import '../data/token_storage.dart';
import '../domain/user_session.dart';

@immutable
abstract class AuthState {
  const AuthState();
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthAuthenticating extends AuthState {
  const AuthAuthenticating();
}

class AuthAuthenticated extends AuthState {
  final UserSession user;
  final String accessToken;

  const AuthAuthenticated({
    required this.user,
    required this.accessToken,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AuthAuthenticated &&
          user == other.user &&
          accessToken == other.accessToken;

  @override
  int get hashCode => user.hashCode ^ accessToken.hashCode;
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

class AuthError extends AuthState {
  final String message;
  const AuthError(this.message);

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is AuthError && message == other.message;

  @override
  int get hashCode => message.hashCode;
}

class AuthController extends StateNotifier<AuthState> {
  final AuthRepository repository;
  final TokenStorage tokenStorage;
  final Ref ref;

  AuthController({
    required this.repository,
    required this.tokenStorage,
    required this.ref,
  }) : super(const AuthInitial()) {
    // Configure ApiClient hooks
    ApiClient().getAccessToken = () {
      final s = state;
      if (s is AuthAuthenticated) {
        return s.accessToken;
      }
      return null;
    };

    ApiClient().onRefreshToken = () async {
      return await _attemptTokenRefresh();
    };
  }

  void _syncDemoRole(String serverRole) {
    switch (serverRole.toUpperCase()) {
      case 'MERCHANT':
        ref.read(demoRoleProvider.notifier).setRole(DemoRole.merchant);
        break;
      case 'ANALYST':
        ref.read(demoRoleProvider.notifier).setRole(DemoRole.analyst);
        break;
      case 'ADMIN':
        ref.read(demoRoleProvider.notifier).setRole(DemoRole.admin);
        break;
    }
  }

  Future<bool> login(String email, String password) async {
    state = const AuthAuthenticating();
    try {
      final res = await repository.login(email, password);
      await tokenStorage.saveTokens(
        accessToken: res.accessToken,
        refreshToken: res.refreshToken,
      );
      _syncDemoRole(res.user.role);
      state = AuthAuthenticated(
        user: res.user,
        accessToken: res.accessToken,
      );
      return true;
    } catch (e) {
      final msg = e is HttpException ? e.message : e.toString();
      state = AuthError(msg);
      return false;
    }
  }

  Future<void> logout() async {
    try {
      final refreshToken = await tokenStorage.getRefreshToken();
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await repository.logout(refreshToken);
      }
    } catch (_) {
      // Ignore network/server errors during logout to guarantee client teardown
    } finally {
      await tokenStorage.clearTokens();
      state = const AuthUnauthenticated();
    }
  }

  Future<bool> _attemptTokenRefresh() async {
    final storedRefresh = await tokenStorage.getRefreshToken();
    if (storedRefresh == null || storedRefresh.isEmpty) {
      await logout();
      return false;
    }

    try {
      final res = await repository.refreshToken(storedRefresh);
      await tokenStorage.saveTokens(
        accessToken: res.accessToken,
        refreshToken: res.refreshToken,
      );
      final current = state;
      if (current is AuthAuthenticated) {
        state = AuthAuthenticated(
          user: current.user,
          accessToken: res.accessToken,
        );
      } else {
        _syncDemoRole(res.user.role);
        state = AuthAuthenticated(
          user: res.user,
          accessToken: res.accessToken,
        );
      }
      return true;
    } catch (_) {
      await logout();
      return false;
    }
  }

  Future<void> checkAuthStatus() async {
    final access = await tokenStorage.getAccessToken();
    final refresh = await tokenStorage.getRefreshToken();

    if (access == null || refresh == null) {
      state = const AuthUnauthenticated();
      return;
    }

    try {
      // Validate token with backend /auth/me
      final user = await repository.getCurrentUser();
      _syncDemoRole(user.role);
      state = AuthAuthenticated(user: user, accessToken: access);
    } catch (_) {
      // Access token may be expired; attempt refresh
      final refreshed = await _attemptTokenRefresh();
      if (!refreshed) {
        state = const AuthUnauthenticated();
      }
    }
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);
  return AuthController(
    repository: repository,
    tokenStorage: tokenStorage,
    ref: ref,
  );
});
