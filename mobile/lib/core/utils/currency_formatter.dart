import 'package:intl/intl.dart';

class CurrencyFormatter {
  static final NumberFormat _bdtFormat = NumberFormat.currency(
    symbol: '৳ ',
    decimalDigits: 2,
  );

  static final NumberFormat _compactBdtFormat = NumberFormat.currency(
    symbol: '৳ ',
    decimalDigits: 0,
  );

  /// Formats amount in Bangladeshi Taka (e.g. ৳ 12,500.00)
  static String formatBdt(double amount) {
    return _bdtFormat.format(amount);
  }

  /// Compact format for large amounts (e.g. ৳ 482,500)
  static String formatBdtCompact(double amount) {
    return _compactBdtFormat.format(amount);
  }
}
