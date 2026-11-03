import 'package:flutter/material.dart';

/// Centralized Design Tokens for PayShield "Precision Sentinel" Theme.
///
/// Every text/surface combination is mathematically verified to satisfy
/// WCAG AA (>= 4.5:1) or AAA (>= 7.0:1) contrast standards.
class AppColors {
  // ---------------------------------------------------------------------------
  // Light Palette ("Warm Alabaster")
  // ---------------------------------------------------------------------------
  static const Color lightCanvas = Color(0xFFF8F9FA);
  static const Color lightSurfacePrimary = Color(0xFFFFFFFF);
  static const Color lightSurfaceSecondary = Color(0xFFF1F3F5);
  static const Color lightBorderSubtle = Color(0xFFE2E8F0);
  static const Color lightBorderStrong = Color(0xFF0369A1);

  static const Color lightTextPrimary = Color(0xFF0F172A); // 16.94:1 AAA
  static const Color lightTextSecondary = Color(0xFF334155); // 9.82:1 AAA
  static const Color lightTextTertiary = Color(0xFF475569); // 7.19:1 AAA
  static const Color lightBrandAccent = Color(0xFF0369A1); // 5.63:1 AA

  // ---------------------------------------------------------------------------
  // Dark Palette ("Obsidian Void")
  // ---------------------------------------------------------------------------
  static const Color darkCanvas = Color(0xFF0B0F17);
  static const Color darkSurfacePrimary = Color(0xFF131B26);
  static const Color darkSurfaceSecondary = Color(0xFF1A2433);
  static const Color darkBorderSubtle = Color(0xFF1F2937);
  static const Color darkBorderStrong = Color(0xFF38BDF8);

  static const Color darkTextPrimary = Color(0xFFF8FAFC); // 18.33:1 AAA
  static const Color darkTextSecondary = Color(0xFFCBD5E1); // 12.92:1 AAA
  static const Color darkTextTertiary = Color(0xFF94A3B8); // 7.48:1 AAA
  static const Color darkBrandAccent = Color(0xFF38BDF8); // 8.95:1 AAA

  // ---------------------------------------------------------------------------
  // Semantic Telemetry — Low Risk (Approve)
  // ---------------------------------------------------------------------------
  static const Color approveTextLight = Color(0xFF065F46); // 7.29:1 AAA
  static const Color approveBgLight = Color(0xFFECFDF5);
  static const Color approveBorderLight = Color(0xFFA7F3D0);

  static const Color approveTextDark = Color(0xFF34D399); // 9.98:1 AAA
  static const Color approveBgDark = Color(0xFF062D24);
  static const Color approveBorderDark = Color(0xFF059669);

  // ---------------------------------------------------------------------------
  // Semantic Telemetry — Medium Risk (Review)
  // ---------------------------------------------------------------------------
  static const Color reviewTextLight = Color(0xFF92400E); // 6.73:1 AA+
  static const Color reviewBgLight = Color(0xFFFFFBEB);
  static const Color reviewBorderLight = Color(0xFFFDE68A);

  static const Color reviewTextDark = Color(0xFFFBBF24); // 11.49:1 AAA
  static const Color reviewBgDark = Color(0xFF381E08);
  static const Color reviewBorderDark = Color(0xFFD97706);

  // ---------------------------------------------------------------------------
  // Semantic Telemetry — High Risk (Block)
  // ---------------------------------------------------------------------------
  static const Color blockTextLight = Color(0xFF991B1B); // 7.88:1 AAA
  static const Color blockBgLight = Color(0xFFFEF2F2);
  static const Color blockBorderLight = Color(0xFFFECACA);

  static const Color blockTextDark = Color(0xFFF87171); // 6.93:1 AA+
  static const Color blockBgDark = Color(0xFF3D1111);
  static const Color blockBorderDark = Color(0xFFDC2626);
}

/// ThemeExtension allowing convenient access to theme-dependent semantic tokens.
@immutable
class AppCustomColors extends ThemeExtension<AppCustomColors> {
  final Color canvas;
  final Color surfacePrimary;
  final Color surfaceSecondary;
  final Color borderSubtle;
  final Color borderStrong;
  final Color textPrimary;
  final Color textSecondary;
  final Color textTertiary;
  final Color brandAccent;

  final Color approveText;
  final Color approveBg;
  final Color approveBorder;

  final Color reviewText;
  final Color reviewBg;
  final Color reviewBorder;

  final Color blockText;
  final Color blockBg;
  final Color blockBorder;

  const AppCustomColors({
    required this.canvas,
    required this.surfacePrimary,
    required this.surfaceSecondary,
    required this.borderSubtle,
    required this.borderStrong,
    required this.textPrimary,
    required this.textSecondary,
    required this.textTertiary,
    required this.brandAccent,
    required this.approveText,
    required this.approveBg,
    required this.approveBorder,
    required this.reviewText,
    required this.reviewBg,
    required this.reviewBorder,
    required this.blockText,
    required this.blockBg,
    required this.blockBorder,
  });

  static const light = AppCustomColors(
    canvas: AppColors.lightCanvas,
    surfacePrimary: AppColors.lightSurfacePrimary,
    surfaceSecondary: AppColors.lightSurfaceSecondary,
    borderSubtle: AppColors.lightBorderSubtle,
    borderStrong: AppColors.lightBorderStrong,
    textPrimary: AppColors.lightTextPrimary,
    textSecondary: AppColors.lightTextSecondary,
    textTertiary: AppColors.lightTextTertiary,
    brandAccent: AppColors.lightBrandAccent,
    approveText: AppColors.approveTextLight,
    approveBg: AppColors.approveBgLight,
    approveBorder: AppColors.approveBorderLight,
    reviewText: AppColors.reviewTextLight,
    reviewBg: AppColors.reviewBgLight,
    reviewBorder: AppColors.reviewBorderLight,
    blockText: AppColors.blockTextLight,
    blockBg: AppColors.blockBgLight,
    blockBorder: AppColors.blockBorderLight,
  );

  static const dark = AppCustomColors(
    canvas: AppColors.darkCanvas,
    surfacePrimary: AppColors.darkSurfacePrimary,
    surfaceSecondary: AppColors.darkSurfaceSecondary,
    borderSubtle: AppColors.darkBorderSubtle,
    borderStrong: AppColors.darkBorderStrong,
    textPrimary: AppColors.darkTextPrimary,
    textSecondary: AppColors.darkTextSecondary,
    textTertiary: AppColors.darkTextTertiary,
    brandAccent: AppColors.darkBrandAccent,
    approveText: AppColors.approveTextDark,
    approveBg: AppColors.approveBgDark,
    approveBorder: AppColors.approveBorderDark,
    reviewText: AppColors.reviewTextDark,
    reviewBg: AppColors.reviewBgDark,
    reviewBorder: AppColors.reviewBorderDark,
    blockText: AppColors.blockTextDark,
    blockBg: AppColors.blockBgDark,
    blockBorder: AppColors.blockBorderDark,
  );

  @override
  AppCustomColors copyWith({
    Color? canvas,
    Color? surfacePrimary,
    Color? surfaceSecondary,
    Color? borderSubtle,
    Color? borderStrong,
    Color? textPrimary,
    Color? textSecondary,
    Color? textTertiary,
    Color? brandAccent,
    Color? approveText,
    Color? approveBg,
    Color? approveBorder,
    Color? reviewText,
    Color? reviewBg,
    Color? reviewBorder,
    Color? blockText,
    Color? blockBg,
    Color? blockBorder,
  }) {
    return AppCustomColors(
      canvas: canvas ?? this.canvas,
      surfacePrimary: surfacePrimary ?? this.surfacePrimary,
      surfaceSecondary: surfaceSecondary ?? this.surfaceSecondary,
      borderSubtle: borderSubtle ?? this.borderSubtle,
      borderStrong: borderStrong ?? this.borderStrong,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      textTertiary: textTertiary ?? this.textTertiary,
      brandAccent: brandAccent ?? this.brandAccent,
      approveText: approveText ?? this.approveText,
      approveBg: approveBg ?? this.approveBg,
      approveBorder: approveBorder ?? this.approveBorder,
      reviewText: reviewText ?? this.reviewText,
      reviewBg: reviewBg ?? this.reviewBg,
      reviewBorder: reviewBorder ?? this.reviewBorder,
      blockText: blockText ?? this.blockText,
      blockBg: blockBg ?? this.blockBg,
      blockBorder: blockBorder ?? this.blockBorder,
    );
  }

  @override
  AppCustomColors lerp(ThemeExtension<AppCustomColors>? other, double t) {
    if (other is! AppCustomColors) return this;
    return AppCustomColors(
      canvas: Color.lerp(canvas, other.canvas, t)!,
      surfacePrimary: Color.lerp(surfacePrimary, other.surfacePrimary, t)!,
      surfaceSecondary: Color.lerp(surfaceSecondary, other.surfaceSecondary, t)!,
      borderSubtle: Color.lerp(borderSubtle, other.borderSubtle, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textTertiary: Color.lerp(textTertiary, other.textTertiary, t)!,
      brandAccent: Color.lerp(brandAccent, other.brandAccent, t)!,
      approveText: Color.lerp(approveText, other.approveText, t)!,
      approveBg: Color.lerp(approveBg, other.approveBg, t)!,
      approveBorder: Color.lerp(approveBorder, other.approveBorder, t)!,
      reviewText: Color.lerp(reviewText, other.reviewText, t)!,
      reviewBg: Color.lerp(reviewBg, other.reviewBg, t)!,
      reviewBorder: Color.lerp(reviewBorder, other.reviewBorder, t)!,
      blockText: Color.lerp(blockText, other.blockText, t)!,
      blockBg: Color.lerp(blockBg, other.blockBg, t)!,
      blockBorder: Color.lerp(blockBorder, other.blockBorder, t)!,
    );
  }
}
