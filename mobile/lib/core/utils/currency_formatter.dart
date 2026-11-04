import 'package:intl/intl.dart';
import 'money.dart';

class CurrencyFormatter {
  static final NumberFormat _bdtFormat = NumberFormat.currency(
    symbol: '৳ ',
    decimalDigits: 2,
  );

  static final NumberFormat _compactBdtFormat = NumberFormat.currency(
    symbol: '৳ ',
    decimalDigits: 0,
  );

  /// Formats amount in Bangladeshi Taka (e.g. ৳ 12,500.00).
  /// Accepts either decimal-safe [Money] or [num].
  static String formatBdt(dynamic amount) {
    if (amount is Money) {
      return amount.toFormattedBdt();
    }
    if (amount is num) {
      return _bdtFormat.format(amount);
    }
    if (amount is String) {
      return Money.fromDecimalString(amount).toFormattedBdt();
    }
    return '৳ 0.00';
  }

  /// Compact format for large amounts (e.g. ৳ 482,500).
  /// Accepts either decimal-safe [Money] or [num].
  static String formatBdtCompact(dynamic amount) {
    if (amount is Money) {
      return amount.toCompactBdt();
    }
    if (amount is num) {
      return _compactBdtFormat.format(amount);
    }
    if (amount is String) {
      return Money.fromDecimalString(amount).toCompactBdt();
    }
    return '৳ 0';
  }
}
