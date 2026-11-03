import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_colors.dart';
import 'package:mobile/app/theme/theme_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

double _srgbToLin(double c) {
  return c <= 0.04045 ? c / 12.92 : math.pow((c + 0.055) / 1.055, 2.4).toDouble();
}

double _relativeLuminance(Color color) {
  final r = _srgbToLin(color.r);
  final g = _srgbToLin(color.g);
  final b = _srgbToLin(color.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

double _contrastRatio(Color c1, Color c2) {
  final l1 = _relativeLuminance(c1);
  final l2 = _relativeLuminance(c2);
  final lighter = math.max(l1, l2);
  final darker = math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ThemeController Unit Tests', () {
    test('Initializes with system default when no preference is saved', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final controller = ThemeController(prefs);
      expect(controller.state, equals(ThemeMode.system));
    });

    test('Loads saved theme preference synchronously', () async {
      SharedPreferences.setMockInitialValues({'payshield_theme_mode': 'dark'});
      final prefs = await SharedPreferences.getInstance();
      final controller = ThemeController(prefs);
      expect(controller.state, equals(ThemeMode.dark));
    });

    test('Updates and persists theme mode selection', () async {
      SharedPreferences.setMockInitialValues({'payshield_theme_mode': 'light'});
      final prefs = await SharedPreferences.getInstance();
      final controller = ThemeController(prefs);

      await controller.setThemeMode(ThemeMode.dark);
      expect(controller.state, equals(ThemeMode.dark));
      expect(prefs.getString('payshield_theme_mode'), equals('dark'));

      await controller.setThemeMode(ThemeMode.system);
      expect(controller.state, equals(ThemeMode.system));
      expect(prefs.getString('payshield_theme_mode'), equals('system'));
    });
  });

  group('WCAG Contrast Ratios Verification', () {
    test('Light theme text colors satisfy WCAG AA (>= 4.5:1) against canvas', () {
      final canvas = AppColors.lightCanvas;

      final primaryRatio = _contrastRatio(AppColors.lightTextPrimary, canvas);
      final secondaryRatio = _contrastRatio(AppColors.lightTextSecondary, canvas);
      final tertiaryRatio = _contrastRatio(AppColors.lightTextTertiary, canvas);
      final brandRatio = _contrastRatio(AppColors.lightBrandAccent, canvas);

      // Verify WCAG AA (>= 4.5:1) and AAA (>= 7.0:1)
      expect(primaryRatio, greaterThanOrEqualTo(7.0), reason: 'Light Primary text must pass AAA');
      expect(secondaryRatio, greaterThanOrEqualTo(7.0), reason: 'Light Secondary text must pass AAA');
      expect(tertiaryRatio, greaterThanOrEqualTo(4.5), reason: 'Light Tertiary text must pass AA');
      expect(brandRatio, greaterThanOrEqualTo(4.5), reason: 'Light Brand accent must pass AA');
    });

    test('Light theme telemetry labels satisfy WCAG AA against canvas and card', () {
      final canvas = AppColors.lightCanvas;
      expect(_contrastRatio(AppColors.approveTextLight, canvas), greaterThanOrEqualTo(4.5));
      expect(_contrastRatio(AppColors.reviewTextLight, canvas), greaterThanOrEqualTo(4.5));
      expect(_contrastRatio(AppColors.blockTextLight, canvas), greaterThanOrEqualTo(4.5));
    });

    test('Dark theme text colors satisfy WCAG AA (>= 4.5:1) against void canvas and cards', () {
      final canvas = AppColors.darkCanvas;
      final card = AppColors.darkSurfacePrimary;

      expect(_contrastRatio(AppColors.darkTextPrimary, canvas), greaterThanOrEqualTo(7.0));
      expect(_contrastRatio(AppColors.darkTextPrimary, card), greaterThanOrEqualTo(7.0));

      expect(_contrastRatio(AppColors.darkTextSecondary, canvas), greaterThanOrEqualTo(7.0));
      expect(_contrastRatio(AppColors.darkTextSecondary, card), greaterThanOrEqualTo(7.0));

      expect(_contrastRatio(AppColors.darkTextTertiary, canvas), greaterThanOrEqualTo(4.5));
      expect(_contrastRatio(AppColors.darkTextTertiary, card), greaterThanOrEqualTo(4.5));

      expect(_contrastRatio(AppColors.darkBrandAccent, canvas), greaterThanOrEqualTo(4.5));
    });

    test('Dark theme telemetry labels satisfy WCAG AA against dark surfaces', () {
      final canvas = AppColors.darkCanvas;
      expect(_contrastRatio(AppColors.approveTextDark, canvas), greaterThanOrEqualTo(4.5));
      expect(_contrastRatio(AppColors.reviewTextDark, canvas), greaterThanOrEqualTo(4.5));
      expect(_contrastRatio(AppColors.blockTextDark, canvas), greaterThanOrEqualTo(4.5));
    });
  });
}
