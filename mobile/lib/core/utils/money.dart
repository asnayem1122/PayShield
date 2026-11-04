import 'package:intl/intl.dart';

/// Immutable, decimal-safe monetary representation for PayShield.
///
/// Stores financial amounts internally as integer minor units (poisha / cents),
/// where 100 minor units = 1.00 major unit (e.g., 151400 minor units = ৳ 1,514.00).
/// Prevents IEEE 754 floating-point inaccuracies in financial calculations.
/// Enforces PostgreSQL NUMERIC(12, 2) boundaries (up to 10 integer digits and 2 decimals).
class Money implements Comparable<Money> {
  final int minorUnits;

  static final RegExp _decimalPattern = RegExp(r'^-?[0-9]{1,10}\.[0-9]{2}$');

  /// Maximum minor units representing PostgreSQL NUMERIC(12, 2) max: 9,999,999,999.99 BDT
  static const int maxMinorUnits = 999999999999;
  static const int minMinorUnits = -999999999999;

  Money(this.minorUnits) {
    _validateMinorUnits(minorUnits);
  }

  const Money._internal(this.minorUnits);

  factory Money.fromMinorUnits(int minorUnits) {
    _validateMinorUnits(minorUnits);
    return Money(minorUnits);
  }

  static const Money zero = Money._internal(0);

  static void _validateMinorUnits(int units) {
    if (units < minMinorUnits || units > maxMinorUnits) {
      throw ArgumentError.value(
        units,
        'minorUnits',
        'Money minorUnits exceeds NUMERIC(12, 2) bounds [$minMinorUnits, $maxMinorUnits]: $units',
      );
    }
  }

  /// Parse from strict 2-decimal string (e.g. "1250.00", "9999999999.99") without floating-point conversion.
  /// Rejects strings that do not have exactly 2 decimal places, exceed 10 integer digits, contain whitespace, or contain invalid characters.
  factory Money.fromDecimalString(String value) {
    if (!_decimalPattern.hasMatch(value)) {
      throw FormatException(
        'Invalid decimal money format: "$value". Expected 1-10 integer digits and exactly 2 decimal places (e.g., "1250.00").',
      );
    }

    final isNegative = value.startsWith('-');
    final clean = isNegative ? value.substring(1) : value;

    final parts = clean.split('.');
    final major = int.parse(parts[0]);
    final minor = int.parse(parts[1]);

    final total = major * 100 + minor;
    if (total > maxMinorUnits) {
      throw FormatException('Money value exceeds maximum NUMERIC(12, 2) limit: "$value"');
    }

    return Money(isNegative ? -total : total);
  }

  /// Factory from integer major units and optional minor units without floating-point conversion.
  factory Money.fromMajor(int major, [int minor = 0]) {
    if (minor < 0 || minor >= 100) {
      throw ArgumentError.value(minor, 'minor', 'Minor units must be between 0 and 99');
    }
    final total = major * 100 + (major < 0 ? -minor : minor);
    if (total.abs() > maxMinorUnits) {
      throw ArgumentError('Money value exceeds maximum NUMERIC(12, 2) limit: $major.$minor');
    }
    return Money(total);
  }

  bool get isPositive => minorUnits > 0;
  bool get isZero => minorUnits == 0;
  bool get isNegative => minorUnits < 0;

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
    final isNeg = minorUnits < 0;
    final absVal = minorUnits.abs();
    final major = (absVal + 50) ~/ 100;
    final formatted = NumberFormat.currency(symbol: '৳ ', decimalDigits: 0).format(major);
    return isNeg ? '-$formatted' : formatted;
  }

  @override
  String toString() => toDecimalString();

  /// Approximate double for non-financial operations (e.g. charts/gauges).
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
