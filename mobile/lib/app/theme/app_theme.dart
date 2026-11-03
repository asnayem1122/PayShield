import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_spacing.dart';
import 'app_typography.dart';

/// Centralized ThemeData Factory for PayShield
class AppTheme {
  // ---------------------------------------------------------------------------
  // Light Theme Definition
  // ---------------------------------------------------------------------------
  static ThemeData get lightTheme {
    final textTheme = AppTypography.createTextTheme(
      AppColors.lightTextPrimary,
      AppColors.lightTextSecondary,
      AppColors.lightTextTertiary,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.lightCanvas,
      canvasColor: AppColors.lightCanvas,
      colorScheme: const ColorScheme.light(
        primary: AppColors.lightBrandAccent,
        onPrimary: Colors.white,
        surface: AppColors.lightSurfacePrimary,
        onSurface: AppColors.lightTextPrimary,
        error: AppColors.blockTextLight,
        onError: Colors.white,
      ),
      textTheme: textTheme,
      extensions: const [AppCustomColors.light],
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.lightSurfacePrimary,
        foregroundColor: AppColors.lightTextPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: AppColors.lightTextPrimary,
        ),
        shape: Border(
          bottom: BorderSide(color: AppColors.lightBorderSubtle, width: 1),
        ),
      ),
      cardTheme: const CardThemeData(
        color: AppColors.lightSurfacePrimary,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.roundedCard,
          side: BorderSide(color: AppColors.lightBorderSubtle, width: 1),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.lightSurfaceSecondary,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        hintStyle: const TextStyle(
          color: AppColors.lightTextTertiary,
          fontSize: 14,
        ),
        labelStyle: const TextStyle(
          color: AppColors.lightTextSecondary,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
        border: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.lightBorderSubtle, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.lightBorderSubtle, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.lightBorderStrong, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.blockTextLight, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.lightTextPrimary,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.roundedButton,
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.lightTextPrimary,
          elevation: 0,
          minimumSize: const Size(double.infinity, 48),
          side: const BorderSide(color: AppColors.lightBorderSubtle, width: 1),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.roundedButton,
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.lightSurfacePrimary,
        selectedItemColor: AppColors.lightBrandAccent,
        unselectedItemColor: AppColors.lightTextTertiary,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        unselectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.lightBorderSubtle,
        thickness: 1,
        space: 1,
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Dark Theme Definition
  // ---------------------------------------------------------------------------
  static ThemeData get darkTheme {
    final textTheme = AppTypography.createTextTheme(
      AppColors.darkTextPrimary,
      AppColors.darkTextSecondary,
      AppColors.darkTextTertiary,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.darkCanvas,
      canvasColor: AppColors.darkCanvas,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.darkBrandAccent,
        onPrimary: AppColors.darkCanvas,
        surface: AppColors.darkSurfacePrimary,
        onSurface: AppColors.darkTextPrimary,
        error: AppColors.blockTextDark,
        onError: Colors.black,
      ),
      textTheme: textTheme,
      extensions: const [AppCustomColors.dark],
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.darkSurfacePrimary,
        foregroundColor: AppColors.darkTextPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: AppColors.darkTextPrimary,
        ),
        shape: Border(
          bottom: BorderSide(color: AppColors.darkBorderSubtle, width: 1),
        ),
      ),
      cardTheme: const CardThemeData(
        color: AppColors.darkSurfacePrimary,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.roundedCard,
          side: BorderSide(color: AppColors.darkBorderSubtle, width: 1),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.darkSurfaceSecondary,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        hintStyle: const TextStyle(
          color: AppColors.darkTextTertiary,
          fontSize: 14,
        ),
        labelStyle: const TextStyle(
          color: AppColors.darkTextSecondary,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
        border: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.darkBorderSubtle, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.darkBorderSubtle, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.darkBorderStrong, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: AppSpacing.roundedInput,
          borderSide: const BorderSide(color: AppColors.blockTextDark, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.darkTextPrimary,
          foregroundColor: AppColors.darkCanvas,
          elevation: 0,
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.roundedButton,
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.darkTextPrimary,
          elevation: 0,
          minimumSize: const Size(double.infinity, 48),
          side: const BorderSide(color: AppColors.darkBorderSubtle, width: 1),
          shape: RoundedRectangleBorder(
            borderRadius: AppSpacing.roundedButton,
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.darkSurfacePrimary,
        selectedItemColor: AppColors.darkBrandAccent,
        unselectedItemColor: AppColors.darkTextTertiary,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        unselectedLabelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.darkBorderSubtle,
        thickness: 1,
        space: 1,
      ),
    );
  }
}
