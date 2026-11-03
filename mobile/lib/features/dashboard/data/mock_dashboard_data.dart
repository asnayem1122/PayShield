import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/dashboard_kpi.dart';
import '../../transactions/data/mock_transactions.dart';
import '../../../core/config/app_risk_constants.dart';

final dashboardKpiProvider = Provider<DashboardKpi>((ref) {
  final transactions = ref.watch(transactionsProvider);

  double totalVolume = 0;
  int approvedCount = 0;
  int reviewCount = 0;
  int blockedCount = 0;
  int scoreSum = 0;

  for (final tx in transactions) {
    totalVolume += tx.amount;
    scoreSum += tx.riskScore;

    // Check if analyst has marked it or rely on recommended action
    if (tx.analystResolution == 'CONFIRM_FRAUD') {
      blockedCount++;
    } else if (tx.analystResolution == 'MARK_LEGITIMATE') {
      approvedCount++;
    } else {
      switch (tx.recommendedAction) {
        case RiskAction.approve:
          approvedCount++;
          break;
        case RiskAction.review:
          reviewCount++;
          break;
        case RiskAction.block:
          blockedCount++;
          break;
      }
    }
  }

  final totalCount = transactions.length;
  final approvalRate = totalCount == 0 ? 0.0 : (approvedCount / totalCount) * 100;
  final reviewRate = totalCount == 0 ? 0.0 : (reviewCount / totalCount) * 100;
  final blockRate = totalCount == 0 ? 0.0 : (blockedCount / totalCount) * 100;
  final avgScore = totalCount == 0 ? 0 : (scoreSum / totalCount).round();

  return DashboardKpi(
    totalVolume: totalVolume,
    totalCount: totalCount,
    approvedCount: approvedCount,
    reviewCount: reviewCount,
    blockedCount: blockedCount,
    approvalRate: approvalRate,
    reviewRate: reviewRate,
    blockRate: blockRate,
    averageRiskScore: avgScore,
  );
});
