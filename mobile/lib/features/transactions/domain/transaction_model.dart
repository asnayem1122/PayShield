import '../../../core/config/app_risk_constants.dart';

class Transaction {
  final String id;
  final double amount;
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
    // Explicit runtime validation guarantees invalid risk scores (< 0 or > 100)
    // throw ArgumentError even in release builds where assertions are disabled.
    AppRiskConstants.validateScore(riskScore);
  }

  RiskLevel get riskLevel => AppRiskConstants.getLevelForScore(riskScore);
  RiskAction get recommendedAction => AppRiskConstants.getActionForScore(riskScore);

  Transaction copyWith({
    String? id,
    double? amount,
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
