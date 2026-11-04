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
    required dynamic amount,
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
  }) : amount = amount is Money
            ? amount
            : amount is String
                ? Money.fromDecimalString(amount)
                : Money.fromNum(amount as num) {
    // Explicit runtime validation guarantees invalid risk scores (< 0 or > 100)
    // throw ArgumentError even in release builds where assertions are disabled.
    AppRiskConstants.validateScore(riskScore);
  }

  RiskLevel get riskLevel => AppRiskConstants.getLevelForScore(riskScore);
  RiskAction get recommendedAction => AppRiskConstants.getActionForScore(riskScore);

  factory Transaction.fromJson(Map<String, dynamic> json) {
    final ref = (json['reference'] ?? json['id'] ?? '').toString();
    final rawAmount = json['amount'];
    final Money parsedAmount = rawAmount is String
        ? Money.fromDecimalString(rawAmount)
        : rawAmount is num
            ? Money.fromNum(rawAmount)
            : Money.zero;

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

    DateTime parsedDate = DateTime.now();
    if (json['created_at'] != null) {
      parsedDate = DateTime.tryParse(json['created_at'].toString()) ?? parsedDate;
    }

    return Transaction(
      id: ref,
      amount: parsedAmount,
      currency: json['currency']?.toString() ?? 'BDT',
      merchantName: json['counterparty_name']?.toString() ?? 'Shadhin Pay',
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
    dynamic amount,
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
