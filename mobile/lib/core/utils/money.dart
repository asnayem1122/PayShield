import 'package:intl/intl.dart';

/// Immutable, decimal-safe monetary representation for PayShield.
///
/// Stores financial amounts internally as integer minor units (poisha / cents),
/// where 100 minor units = 1.00 major unit (e.g., 151400 minor units = ৳ 1,514.00).
/// Prevents IEEE 754 floating-point inaccuracies in financial aggregation.
class Money implements Comparable<Money> {
  final int minorUnits;

  const Money(this.minorUnits);
  const Money.fromMinorUnits(this.minorUnits);

  static const Money zero = Money(0);

  /// Parse from decimal string e.g. "1514.00" without floating-point conversion.
  factory Money.fromDecimalString(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return Money.zero;

    final isNegative = trimmed.startsWith('-');
    final clean = isNegative ? trimmed.substring(1) : trimmed;

    final parts = clean.split('.');
    final major = int.tryParse(parts[0]) ?? 0;

    int minor = 0;
    if (parts.length > 1) {
      final minorStr = parts[1];
      if (minorStr.length == 1) {
        minor = (int.tryParse(minorStr) ?? 0) * 10;
      } else if (minorStr.length >= 2) {
        minor = int.tryParse(minorStr.substring(0, 2)) ?? 0;
      }
    }

    final total = major * 100 + minor;
    return Money(isNegative ? -total : total);
  }

  /// Factory from integer major units (e.g. 1514 -> 151400 minor units).
  factory Money.fromMajor(int major, [int minor = 0]) {
    return Money(major * 100 + minor);
  }

  /// Factory for num or dynamic input (converts via fixed 2-decimal string).
  factory Money.fromNum(num val) {
    return Money.fromDecimalString(val.toStringAsFixed(2));
  }

  /// Strict wire contract representation: exact 2 decimal places (e.g. "1514.00").
  String toDecimalString() {
    final isNeg = minorUnits < 0;
    final absVal = minorUnits.abs();
    final major = absVal ~/ 100;
    final minor = (absVal % 100).toString().padLeft(2, '0');
    return '${isNeg ? '-' : ''}$major.$minor';
  }

  /// Bangladeshi Taka formatted string (e.g. "৳ 1,514.00").
  String toFormattedBdt() {
    final isNeg = minorUnits < 0;
    final absVal = minorUnits.abs();
    final major = absVal ~/ 100;
    final minor = (absVal % 100).toString().padLeft(2, '0');
    final formattedMajor = NumberFormat('#,##0').format(major);
    return '${isNeg ? '-' : ''}৳ $formattedMajor.$minor';
  }

  /// Compact Bangladeshi Taka formatted string (e.g. "৳ 482,500").
  String toCompactBdt() {
    final major = (minorUnits / 100.0).round();
    final formatted = NumberFormat.currency(symbol: '৳ ', decimalDigits: 0).format(major);
    return formatted;
  }

  @override
  String toString() => toDecimalString();

  /// Approximate double for non-financial operations (e.g. charts).
  double toDouble() => minorUnits / 100.0;

  Money operator +(Money other) => Money(minorUnits + other.minorUnits);
  Money operator -(Money other) => Money(minorUnits - other.minorUnits);
  Money operator *(num multiplier) => Money((minorUnits * multiplier).round());

  bool operator <(Money other) => minorUnits < other.minorUnits;
  bool operator <=(Money other) => minorUnits <= other.minorUnits;
  bool operator >(Money other) => minorUnits > other.minorUnits;
  bool operator >=(Money other) => minorUnits >= other.minorUnits;

  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is Money && other.minorUnits == minorUnits);

  @override
  int get hashCode => minorUnits.hashCode;

  @override
  int compareTo(Money other) => minorUnits.compareTo(other.minorUnits);
}
