import 'package:intl/intl.dart';

class DateFormatter {
  static final DateFormat _dateTimeFormat = DateFormat('MMM dd, yyyy • HH:mm:ss');
  static final DateFormat _shortDateFormat = DateFormat('MMM dd, HH:mm');

  static String formatFull(DateTime dateTime) {
    return _dateTimeFormat.format(dateTime.toLocal());
  }

  static String formatShort(DateTime dateTime) {
    return _shortDateFormat.format(dateTime.toLocal());
  }

  static String formatIso(DateTime dateTime) {
    return dateTime.toUtc().toIso8601String();
  }

  static String relativeTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }
}
