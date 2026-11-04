import '../../../core/config/app_risk_constants.dart';
import '../../../core/utils/money.dart';

class Transaction {
  final String id;
  final Money amount;
  final String currency;
  final String merchantName;
  final String merchantCategory;
  final int riskScore; // Strictly 0 - 100
  final List<String> riskFactors;
  final String deviceModel;
  final bool isNewDevice;
  final String location;
  final int transactionsLastHour;
  final int previousChargebacks;
  final DateTime timestamp;
  final String? analystResolution; // null, CONFIRM_FRAUD, MARK_LEGITIMATE
  final String? analystNotes;

  Transaction({
    required this.id,
    required this.amount,
    this.currency = 'BDT',
    required this.merchantName,
    required this.merchantCategory,
    required this.riskScore,
    required this.riskFactors,
    required this.deviceModel,
    required this.isNewDevice,
    required this.location,
    required this.transactionsLastHour,
    required this.previousChargebacks,
    required this.timestamp,
    this.analystResolution,
    this.analystNotes,
  }) {
    if (amount.minorUnits <= 0) {
      throw ArgumentError(
        'Transaction amount must be strictly positive: got ${amount.toDecimalString()}',
      );
    }
    // Explicit runtime validation guarantees invalid risk scores (< 0 or > 100)
    // throw ArgumentError even in release builds where assertions are disabled.
    AppRiskConstants.validateScore(riskScore);
  }

  RiskLevel get riskLevel => AppRiskConstants.getLevelForScore(riskScore);
  RiskAction get recommendedAction => AppRiskConstants.getActionForScore(riskScore);

  static final RegExp transactionWireAmountPattern = RegExp(r'^[0-9]{1,10}\.[0-9]{2}$');

  factory Transaction.fromJson(Map<String, dynamic> json) {
    final ref = (json['reference'] ?? json['id'] ?? '').toString();
    if (!json.containsKey('amount') || json['amount'] == null) {
      throw const FormatException('Transaction JSON missing mandatory "amount" field');
    }
    final rawAmount = json['amount'];
    if (rawAmount is! String) {
      throw FormatException(
        'Transaction "amount" must be a JSON string, got ${rawAmount.runtimeType}: $rawAmount',
      );
    }
    if (!transactionWireAmountPattern.hasMatch(rawAmount)) {
      throw FormatException(
        'Transaction amount wire format invalid: "$rawAmount". Must match ^[0-9]{1,10}\\.[0-9]{2}\$ without whitespace, negative signs, or scientific notation.',
      );
    }
    final Money parsedAmount = Money.fromDecimalString(rawAmount);
    if (parsedAmount.minorUnits <= 0) {
      throw FormatException(
        'Transaction amount must be strictly positive, got "$rawAmount"',
      );
    }

    final score = (json['risk_score'] as num?)?.toInt() ?? 10;
    final clampedScore = score.clamp(0, 100);

    final rawFactors = json['risk_factors'];
    List<String> factors = [];
    if (rawFactors is List) {
      factors = rawFactors.map((e) => e.toString()).toList();
    }

    final rawStatus = json['transaction_status']?.toString();
    String? resolution;
    if (rawStatus == 'BLOCKED') {
      resolution = 'CONFIRM_FRAUD';
    } else if (rawStatus == 'APPROVED') {
      resolution = 'MARK_LEGITIMATE';
    }

    DateTime parsedDate = DateTime.now().toUtc();
    if (json['created_at'] != null) {
      parsedDate = DateTime.tryParse(json['created_at'].toString())?.toUtc() ?? parsedDate;
    }

    return Transaction(
      id: ref,
      amount: parsedAmount,
      currency: json['currency']?.toString() ?? 'BDT',
      merchantName: json['counterparty_name']?.toString() ?? 'PayShield Demo Merchant',
      merchantCategory: 'Retail',
      riskScore: clampedScore,
      riskFactors: factors,
      deviceModel: json['device_model']?.toString() ?? 'Mobile Client',
      isNewDevice: json['is_new_device'] == true,
      location: json['location_city']?.toString() ?? 'Dhaka',
      transactionsLastHour: (json['transactions_last_hour'] as num?)?.toInt() ?? 0,
      previousChargebacks: (json['previous_chargebacks'] as num?)?.toInt() ?? 0,
      timestamp: parsedDate,
      analystResolution: resolution,
      analystNotes: json['resolution_note']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'reference': id,
      'amount': amount.toDecimalString(),
      'currency': currency,
      'counterparty_name': merchantName,
      'channel': 'MOBILE_APP',
      'device_model': deviceModel,
      'location_city': location,
      'is_location_anomaly': false,
      'risk_score': riskScore,
      'risk_level': riskLevel.name.toUpperCase(),
      'recommended_action': recommendedAction.name.toUpperCase(),
      'transaction_status': analystResolution == 'CONFIRM_FRAUD'
          ? 'BLOCKED'
          : analystResolution == 'MARK_LEGITIMATE'
              ? 'APPROVED'
              : 'REVIEW',
      'created_at': timestamp.toIso8601String(),
    };
  }

  Transaction copyWith({
    String? id,
    Money? amount,
    String? currency,
    String? merchantName,
    String? merchantCategory,
    int? riskScore,
    List<String>? riskFactors,
    String? deviceModel,
    bool? isNewDevice,
    String? location,
    int? transactionsLastHour,
    int? previousChargebacks,
    DateTime? timestamp,
    String? analystResolution,
    String? analystNotes,
  }) {
    return Transaction(
      id: id ?? this.id,
      amount: amount ?? this.amount,
      currency: currency ?? this.currency,
      merchantName: merchantName ?? this.merchantName,
      merchantCategory: merchantCategory ?? this.merchantCategory,
      riskScore: riskScore ?? this.riskScore,
      riskFactors: riskFactors ?? this.riskFactors,
      deviceModel: deviceModel ?? this.deviceModel,
      isNewDevice: isNewDevice ?? this.isNewDevice,
      location: location ?? this.location,
      transactionsLastHour: transactionsLastHour ?? this.transactionsLastHour,
      previousChargebacks: previousChargebacks ?? this.previousChargebacks,
      timestamp: timestamp ?? this.timestamp,
      analystResolution: analystResolution ?? this.analystResolution,
      analystNotes: analystNotes ?? this.analystNotes,
    );
  }
}
