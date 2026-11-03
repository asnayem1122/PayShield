import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../core/config/app_risk_constants.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/risk_badge.dart';
import '../../../core/widgets/score_gauge.dart';
import '../../../core/widgets/simulation_disclaimer_banner.dart';
import '../../transactions/data/mock_transactions.dart';

class RiskIndicatorsScreen extends ConsumerWidget {
  final String transactionId;

  const RiskIndicatorsScreen({
    super.key,
    required this.transactionId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final transactions = ref.watch(transactionsProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    final tx = transactions.firstWhere(
      (item) => item.id == transactionId,
      orElse: () => transactions.first,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Risk Indicators & Factors'),
      ),
      body: SafeArea(
        child: ListView(
          padding: AppSpacing.screenPadding,
          children: [
            const SimulationDisclaimerBanner(
              text: 'Academic Demonstration — Risk scores and factor weights are simulated heuristics.',
            ),
            const SizedBox(height: AppSpacing.md),

            // Score Header Bento
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Risk Evaluation',
                        style: theme.textTheme.titleMedium,
                      ),
                      RiskBadge(action: tx.recommendedAction),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  ScoreGauge(score: tx.riskScore),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'Evaluated ${DateFormatter.formatShort(tx.timestamp)} for ${tx.merchantName}',
                    style: TextStyle(fontSize: 11, color: colors.textTertiary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Feature Contributions Card (Illustrative Simulated Explanations)
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Factor Contribution Weights',
                        style: theme.textTheme.titleSmall,
                      ),
                      Icon(Icons.tune_rounded, size: 16, color: colors.brandAccent),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    AppRiskConstants.featureExplanationDisclaimer,
                    style: TextStyle(
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                      color: colors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  if (tx.riskScore > 74) ...[
                    _buildFactorBar('Unrecognized New Device', 35, colors.blockText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('High 1-Hour Velocity (${tx.transactionsLastHour} tx)', 30, colors.blockText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('Location Anomaly (${tx.location})', 26, colors.reviewText, colors),
                  ] else if (tx.riskScore > 39) ...[
                    _buildFactorBar('Unusual Transaction Amount', 28, colors.reviewText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('Time-of-Day Deviation', 18, colors.reviewText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('Device Match Stability', 8, colors.approveText, colors),
                  ] else ...[
                    _buildFactorBar('Verified Trusted Device', 5, colors.approveText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('Familiar Geolocation', 4, colors.approveText, colors),
                    const SizedBox(height: AppSpacing.sm),
                    _buildFactorBar('Clean Chargeback History', 2, colors.approveText, colors),
                  ],
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Policy Recommendation Box
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Policy Recommendation', style: theme.textTheme.titleSmall),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    tx.recommendedAction == RiskAction.block
                        ? 'Recommendation: BLOCK. The risk score (${tx.riskScore}/100) exceeds the high-risk policy threshold of 75. In the demo workflow, this transaction is marked blocked.'
                        : tx.recommendedAction == RiskAction.review
                            ? 'Recommendation: REVIEW. The risk score (${tx.riskScore}/100) falls between 40 and 74. It has been routed to the Analyst Review Queue.'
                            : 'Recommendation: APPROVE. The risk score (${tx.riskScore}/100) is within safe limits (0 - 39). Transaction cleared without friction.',
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.4,
                      color: colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'Architectural Notice: The final fraud decision must be calculated on the backend. Flutter displays this estimate strictly for monitoring.',
                    style: TextStyle(
                      fontSize: 11,
                      color: colors.textTertiary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFactorBar(
    String factorName,
    int weightPoints,
    Color indicatorColor,
    AppCustomColors colors,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                factorName,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Text(
              '+$weightPoints pts',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: indicatorColor,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: LinearProgressIndicator(
            value: (weightPoints / 40.0).clamp(0.05, 1.0),
            minHeight: 6,
            backgroundColor: colors.surfaceSecondary,
            valueColor: AlwaysStoppedAnimation<Color>(indicatorColor),
          ),
        ),
      ],
    );
  }
}
