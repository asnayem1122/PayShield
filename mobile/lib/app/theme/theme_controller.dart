import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Injected SharedPreferences provider (overridden synchronously in main.dart)
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('sharedPreferencesProvider must be overridden in ProviderScope');
});

final themeControllerProvider = StateNotifierProvider<ThemeController, ThemeMode>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return ThemeController(prefs);
});

class ThemeController extends StateNotifier<ThemeMode> {
  static const String _prefKey = 'payshield_theme_mode';
  final SharedPreferences _prefs;

  ThemeController(this._prefs) : super(_loadInitialMode(_prefs));

  static ThemeMode _loadInitialMode(SharedPreferences prefs) {
    final saved = prefs.getString(_prefKey);
    switch (saved) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      case 'system':
      default:
        return ThemeMode.system;
    }
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = mode;
    String modeString;
    switch (mode) {
      case ThemeMode.light:
        modeString = 'light';
        break;
      case ThemeMode.dark:
        modeString = 'dark';
        break;
      case ThemeMode.system:
        modeString = 'system';
        break;
    }
    await _prefs.setString(_prefKey, modeString);
  }
}
