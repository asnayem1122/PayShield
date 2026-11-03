import 'package:flutter/material.dart';

/// Typography Scale for PayShield "Precision Sentinel"
class AppTypography {
  // Tabular feature list to prevent number jitter
  static const List<FontFeature> tabularFigures = [
    FontFeature.tabularFigures(),
  ];

  static TextTheme createTextTheme(Color primary, Color secondary, Color tertiary) {
    return TextTheme(
      displayLarge: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.6,
        color: primary,
        fontFeatures: tabularFigures,
      ),
      displayMedium: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.5,
        color: primary,
        fontFeatures: tabularFigures,
      ),
      headlineSmall: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.3,
        color: primary,
      ),
      titleMedium: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        letterSpacing: -0.1,
        color: primary,
      ),
      titleSmall: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.0,
        color: primary,
      ),
      bodyLarge: TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w400,
        height: 1.5,
        color: primary,
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        height: 1.45,
        color: secondary,
      ),
      bodySmall: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w400,
        height: 1.4,
        color: tertiary,
      ),
      labelLarge: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.1,
        color: primary,
      ),
      labelSmall: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 0.6,
        color: tertiary,
      ),
    );
  }

  // Monospace data style for financial amounts, risk scores, hashes, and velocity
  static TextStyle monospaceData({
    required BuildContext context,
    double fontSize = 14,
    FontWeight fontWeight = FontWeight.w600,
    Color? color,
  }) {
    final theme = Theme.of(context);
    return TextStyle(
      fontFamily: 'monospace',
      fontSize: fontSize,
      fontWeight: fontWeight,
      fontFeatures: tabularFigures,
      color: color ?? theme.textTheme.bodyLarge?.color,
    );
  }
}
