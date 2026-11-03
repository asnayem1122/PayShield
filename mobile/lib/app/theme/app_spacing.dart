import 'package:flutter/material.dart';

/// 4dp Base Spacing Scale & Geometry Radii
class AppSpacing {
  // Base spacing scale (multiples of 4dp)
  static const double xxs = 4.0; // 1x
  static const double xs = 8.0; // 2x
  static const double sm = 12.0; // 3x
  static const double md = 16.0; // 4x (standard screen padding & card inset)
  static const double lg = 24.0; // 6x (section division)
  static const double xl = 32.0; // 8x (macro-whitespace)
  static const double xxl = 48.0; // 12x (empty state & auth forms)

  // Insets shortcuts
  static const EdgeInsets screenPadding = EdgeInsets.all(md);
  static const EdgeInsets cardPadding = EdgeInsets.all(md);
  static const EdgeInsets compactPadding = EdgeInsets.all(sm);
  static const EdgeInsets microPadding = EdgeInsets.symmetric(
    horizontal: xs,
    vertical: xxs,
  );

  // Geometry: Radii
  static const double radiusCard = 12.0;
  static const double radiusButton = 8.0;
  static const double radiusInput = 8.0;
  static const double radiusBadge = 6.0;

  static const BorderRadius roundedCard = BorderRadius.all(
    Radius.circular(radiusCard),
  );
  static const BorderRadius roundedButton = BorderRadius.all(
    Radius.circular(radiusButton),
  );
  static const BorderRadius roundedInput = BorderRadius.all(
    Radius.circular(radiusInput),
  );
  static const BorderRadius roundedBadge = BorderRadius.all(
    Radius.circular(radiusBadge),
  );
}
