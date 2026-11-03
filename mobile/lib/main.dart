import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'app/app.dart';
import 'app/theme/theme_controller.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Pre-load SharedPreferences before mounting root widget tree to eliminate theme flashing
  final sharedPreferences = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [
        sharedPreferencesProvider.overrideWithValue(sharedPreferences),
      ],
      child: const PayShieldApp(),
    ),
  );
}
