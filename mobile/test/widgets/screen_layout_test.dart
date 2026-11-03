import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/app/theme/theme_controller.dart';
import 'package:mobile/core/config/app_risk_constants.dart';
import 'package:mobile/core/widgets/risk_badge.dart';
import 'package:mobile/features/auth/presentation/login_screen.dart';
import 'package:mobile/features/dashboard/presentation/dashboard_screen.dart';
import 'package:mobile/features/transactions/presentation/transaction_details_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

Widget createTestApp({
  required Widget child,
  required SharedPreferences prefs,
  ThemeMode mode = ThemeMode.light,
  TextScaler textScaler = TextScaler.noScaling,
}) {
  return ProviderScope(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(prefs),
    ],
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: mode,
      home: MediaQuery(
        data: MediaQueryData(textScaler: textScaler),
        child: child,
      ),
    ),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late SharedPreferences prefs;

  setUp(() async {
    SharedPreferences.setMockInitialValues({'payshield_theme_mode': 'light'});
    prefs = await SharedPreferences.getInstance();
  });

  group('Small Screen (320x568 dp) Overflow Verification', () {
    testWidgets('Dashboard renders on compact screen without overflow', (tester) async {
      tester.view.physicalSize = const Size(320 * 2.0, 568 * 2.0);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        createTestApp(
          child: const DashboardScreen(),
          prefs: prefs,
        ),
      );
      await tester.pumpAndSettle();

      final exc = tester.takeException();
      if (exc != null && exc is FlutterError) {
        debugPrint(exc.toString());
      }
      expect(exc, isNull);
      expect(find.text('Total Simulated Volume (Today)'), findsOneWidget);
    });

    testWidgets('LoginScreen renders on compact screen without overflow', (tester) async {
      tester.view.physicalSize = const Size(320 * 2.0, 568 * 2.0);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        createTestApp(
          child: const LoginScreen(),
          prefs: prefs,
        ),
      );
      await tester.pumpAndSettle();

      final exc = tester.takeException();
      if (exc != null && exc is FlutterError) {
        debugPrint(exc.toString());
      }
      expect(exc, isNull);
      expect(find.text('Sign In to Console'), findsOneWidget);
    });

    testWidgets('TransactionDetailsScreen renders without overflow', (tester) async {
      tester.view.physicalSize = const Size(320 * 2.0, 568 * 2.0);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        createTestApp(
          child: const TransactionDetailsScreen(transactionId: 'tx_c6b8d0f2_block'),
          prefs: prefs,
        ),
      );
      await tester.pumpAndSettle();

      final exc = tester.takeException();
      if (exc != null && exc is FlutterError) {
        debugPrint(exc.toString());
      }
      expect(exc, isNull);
      expect(find.text('Transaction Details'), findsOneWidget);
    });
  });

  group('WCAG Large Text Scaling (1.5x) Verification', () {
    testWidgets('Dashboard scales cleanly under 1.5x text scaler', (tester) async {
      await tester.pumpWidget(
        createTestApp(
          child: const DashboardScreen(),
          prefs: prefs,
          textScaler: const TextScaler.linear(1.5),
        ),
      );
      await tester.pumpAndSettle();

      final exc = tester.takeException();
      if (exc != null && exc is FlutterError) {
        debugPrint(exc.toString());
      }
      expect(exc, isNull);
    });
  });

  group('Accessibility & Semantics Verification', () {
    testWidgets('RiskBadge provides explicit semantic accessibility labels', (tester) async {
      await tester.pumpWidget(
        createTestApp(
          child: const Scaffold(
            body: Column(
              children: [
                RiskBadge(action: RiskAction.approve),
                RiskBadge(action: RiskAction.review),
                RiskBadge(action: RiskAction.block),
              ],
            ),
          ),
          prefs: prefs,
        ),
      );
      await tester.pumpAndSettle();

      expect(find.bySemanticsLabel('Risk decision: APPROVE'), findsOneWidget);
      expect(find.bySemanticsLabel('Risk decision: REVIEW'), findsOneWidget);
      expect(find.bySemanticsLabel('Risk decision: BLOCK'), findsOneWidget);
    });
  });
}
