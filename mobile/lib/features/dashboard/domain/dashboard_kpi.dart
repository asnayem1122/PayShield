import '../../../core/utils/money.dart';

class DashboardKpi {
  final Money totalVolume;
  final int totalCount;
  final int approvedCount;
  final int reviewCount;
  final int blockedCount;
  final double approvalRate;
  final double reviewRate;
  final double blockRate;
  final int averageRiskScore;

  DashboardKpi({
    required this.totalVolume,
    required this.totalCount,
    required this.approvedCount,
    required this.reviewCount,
    required this.blockedCount,
    required this.approvalRate,
    required this.reviewRate,
    required this.blockRate,
    required this.averageRiskScore,
  });
}
