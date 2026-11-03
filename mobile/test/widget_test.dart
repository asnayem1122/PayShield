import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/app.dart';
import 'package:mobile/app/theme/theme_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('PayShieldApp initial smoke test mounts Dashboard', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({'payshield_theme_mode': 'system'});
    final prefs = await SharedPreferences.getInstance();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sharedPreferencesProvider.overrideWithValue(prefs),
        ],
        child: const PayShieldApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify PayShield brand name and core dashboard elements are mounted
    expect(find.text('PayShield'), findsOneWidget);
    expect(find.text('Total Simulated Volume (Today)'), findsOneWidget);
  });
}
