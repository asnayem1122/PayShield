import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/role/demo_role.dart';
import 'package:mobile/features/auth/data/auth_repository.dart';
import 'package:mobile/features/auth/data/token_storage.dart';
import 'package:mobile/features/auth/domain/user_session.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';

class MockAuthRepository extends AuthRepository {
  bool shouldFail = false;
  bool shouldFailLogout = false;
  String failMessage = 'Invalid email or password';

  @override
  Future<AuthResponse> login(String email, String password) async {
    if (shouldFail) {
      throw HttpException(failMessage, statusCode: 401);
    }
    final role = email.contains('merchant')
        ? 'MERCHANT'
        : email.contains('analyst')
            ? 'ANALYST'
            : 'ADMIN';

    return AuthResponse(
      accessToken: 'mock_jwt_access_token_123',
      refreshToken: 'mock_jwt_refresh_token_456',
      expiresIn: 900,
      user: UserSession(
        id: 'usr_mock_111',
        email: email,
        fullName: 'Mock User',
        role: role,
        status: 'ACTIVE',
        merchantId: role == 'MERCHANT' ? 'merch_demo_123' : null,
      ),
    );
  }

  @override
  Future<UserSession> getCurrentUser() async {
    if (shouldFail) {
      throw HttpException('Unauthorized', statusCode: 401);
    }
    return const UserSession(
      id: 'usr_mock_111',
      email: 'analyst.shafiq@payshield.internal',
      fullName: 'Shafiqul Islam',
      role: 'ANALYST',
      status: 'ACTIVE',
    );
  }

  @override
  Future<AuthResponse> refreshToken(String refreshToken) async {
    if (shouldFail) {
      throw HttpException('Revoked', statusCode: 401);
    }
    return const AuthResponse(
      accessToken: 'mock_jwt_access_new',
      refreshToken: 'mock_jwt_refresh_new',
      expiresIn: 900,
      user: UserSession(
        id: 'usr_mock_111',
        email: 'analyst.shafiq@payshield.internal',
        fullName: 'Shafiqul Islam',
        role: 'ANALYST',
        status: 'ACTIVE',
      ),
    );
  }

  @override
  Future<void> logout(String? refreshToken) async {
    if (shouldFailLogout) {
      throw HttpException('Server Error', statusCode: 500);
    }
  }
}

void main() {
  group('TokenStorage Unit Tests', () {
    test('InMemoryTokenStorage stores, retrieves, and clears tokens', () async {
      final storage = InMemoryTokenStorage();
      expect(await storage.getAccessToken(), isNull);
      expect(await storage.getRefreshToken(), isNull);

      await storage.saveTokens(
        accessToken: 'access_1',
        refreshToken: 'refresh_1',
      );

      expect(await storage.getAccessToken(), equals('access_1'));
      expect(await storage.getRefreshToken(), equals('refresh_1'));

      await storage.clearTokens();
      expect(await storage.getAccessToken(), isNull);
      expect(await storage.getRefreshToken(), isNull);
    });
  });

  group('UserSession Domain Unit Tests', () {
    test('Correctly parses JSON into UserSession and checks role getters', () {
      final json = {
        'id': 'usr_test_123',
        'email': 'merchant@test.com',
        'full_name': 'Test Merchant',
        'role': 'MERCHANT',
        'status': 'ACTIVE',
        'merchant_id': 'm_001',
        'merchant_name': 'Test Store',
      };

      final session = UserSession.fromJson(json);
      expect(session.id, equals('usr_test_123'));
      expect(session.email, equals('merchant@test.com'));
      expect(session.isMerchant, isTrue);
      expect(session.isAnalyst, isFalse);
      expect(session.isAdmin, isFalse);
    });

    test('Checks analyst and admin role getters correctly', () {
      const analyst = UserSession(
        id: '1',
        email: 'a@p.internal',
        fullName: 'A',
        role: 'ANALYST',
        status: 'ACTIVE',
      );
      expect(analyst.isAnalyst, isTrue);
      expect(analyst.isMerchant, isFalse);

      const admin = UserSession(
        id: '2',
        email: 'admin@p.internal',
        fullName: 'Admin',
        role: 'ADMIN',
        status: 'ACTIVE',
      );
      expect(admin.isAdmin, isTrue);
      expect(admin.isAnalyst, isFalse);
    });
  });

  group('AuthController Riverpod Unit Tests', () {
    late ProviderContainer container;
    late MockAuthRepository mockRepo;
    late InMemoryTokenStorage memoryStorage;

    setUp(() {
      mockRepo = MockAuthRepository();
      memoryStorage = InMemoryTokenStorage();

      container = ProviderContainer(
        overrides: [
          authRepositoryProvider.overrideWithValue(mockRepo),
          tokenStorageProvider.overrideWithValue(memoryStorage),
        ],
      );
    });

    tearDown(() {
      container.dispose();
    });

    test('Initial state is AuthInitial', () {
      final state = container.read(authControllerProvider);
      expect(state, isA<AuthInitial>());
    });

    test('Successful login saves tokens, updates state and synchronizes demoRole', () async {
      final controller = container.read(authControllerProvider.notifier);

      final success = await controller.login(
        'analyst.shafiq@payshield.internal',
        'TestSecretPassword123!',
      );

      expect(success, isTrue);
      final state = container.read(authControllerProvider);
      expect(state, isA<AuthAuthenticated>());
      final auth = state as AuthAuthenticated;
      expect(auth.user.email, equals('analyst.shafiq@payshield.internal'));
      expect(auth.user.role, equals('ANALYST'));
      expect(auth.accessToken, equals('mock_jwt_access_token_123'));

      expect(await memoryStorage.getAccessToken(), equals('mock_jwt_access_token_123'));
      expect(container.read(demoRoleProvider), equals(DemoRole.analyst));
    });

    test('Failed login sets AuthError state and does not store tokens', () async {
      mockRepo.shouldFail = true;
      mockRepo.failMessage = 'Invalid email or password';
      final controller = container.read(authControllerProvider.notifier);

      final success = await controller.login(
        'merchant@techpulse.bd',
        'WrongPassword',
      );

      expect(success, isFalse);
      final state = container.read(authControllerProvider);
      expect(state, isA<AuthError>());
      final err = state as AuthError;
      expect(err.message, equals('Invalid email or password'));
      expect(await memoryStorage.getAccessToken(), isNull);
    });

    test('Logout clears tokens and transitions to AuthUnauthenticated', () async {
      final controller = container.read(authControllerProvider.notifier);
      await controller.login('merchant@techpulse.bd', 'TestSecretPassword123!');
      expect(container.read(authControllerProvider), isA<AuthAuthenticated>());

      await controller.logout();
      expect(container.read(authControllerProvider), isA<AuthUnauthenticated>());
      expect(await memoryStorage.getAccessToken(), isNull);
      expect(await memoryStorage.getRefreshToken(), isNull);
    });

    test('Logout clears tokens and transitions to AuthUnauthenticated even on backend error', () async {
      mockRepo.shouldFailLogout = true;
      final controller = container.read(authControllerProvider.notifier);
      await controller.login('merchant@techpulse.bd', 'TestSecretPassword123!');
      expect(container.read(authControllerProvider), isA<AuthAuthenticated>());

      await controller.logout();
      expect(container.read(authControllerProvider), isA<AuthUnauthenticated>());
      expect(await memoryStorage.getAccessToken(), isNull);
      expect(await memoryStorage.getRefreshToken(), isNull);
    });

    test('checkAuthStatus restores session when valid tokens exist', () async {
      await memoryStorage.saveTokens(
        accessToken: 'valid_access_token',
        refreshToken: 'valid_refresh_token',
      );

      final controller = container.read(authControllerProvider.notifier);
      await controller.checkAuthStatus();

      final state = container.read(authControllerProvider);
      expect(state, isA<AuthAuthenticated>());
      final auth = state as AuthAuthenticated;
      expect(auth.user.role, equals('ANALYST'));
      expect(container.read(demoRoleProvider), equals(DemoRole.analyst));
    });
  });
}
