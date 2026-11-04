import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../app/theme/app_typography.dart';
import '../../../core/config/app_risk_constants.dart';
import '../../../core/role/demo_role.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/metric_bento.dart';
import '../../../core/widgets/risk_badge.dart';
import '../../../core/widgets/simulation_disclaimer_banner.dart';
import '../../transactions/data/mock_transactions.dart';
import '../../transactions/domain/transaction_model.dart';
import '../data/mock_dashboard_data.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final kpi = ref.watch(dashboardKpiProvider);
    final transactions = ref.watch(transactionsProvider);
    final activeRole = ref.watch(demoRoleProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    // Recent transactions (top 5)
    final recentTransactions = transactions.take(5).toList();

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () async {
          await ref.read(transactionsProvider.notifier).fetchFromBackend();
        },
        child: ListView(
          padding: AppSpacing.screenPadding,
          children: [
            // Role Context Header (responsive with Expanded)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${activeRole.displayName} Overview',
                        style: theme.textTheme.headlineSmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        'Daily Risk Telemetry & Settlement',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: colors.textSecondary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.xs),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: colors.surfaceSecondary,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: colors.borderSubtle, width: 1),
                  ),
                  child: Text(
                    'SIMULATED LIVE',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                      color: colors.brandAccent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),

            const SimulationDisclaimerBanner(),
            const SizedBox(height: AppSpacing.md),

            // Primary Volume Bento Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          'Total Simulated Volume (Today)',
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: colors.textSecondary,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Icon(Icons.payments_outlined, size: 16, color: colors.brandAccent),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    CurrencyFormatter.formatBdt(kpi.totalVolume),
                    style: AppTypography.monospaceData(
                      context: context,
                      fontSize: 28,
                      fontWeight: FontWeight.w700,
                      color: colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    'Reconciled from ${kpi.totalCount} synthetic payment transactions',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: colors.textTertiary,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Responsive Bento Metric Cards
            LayoutBuilder(
              builder: (context, constraints) {
                if (constraints.maxWidth < 360) {
                  return Column(
                    children: [
                      MetricBento(
                        title: 'Approved',
                        metric: '${kpi.approvedCount}',
                        subtitle: '${kpi.approvalRate.toStringAsFixed(1)}% rate',
                        accentColor: colors.approveText,
                        icon: Icons.check_circle_outline_rounded,
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Row(
                        children: [
                          Expanded(
                            child: MetricBento(
                              title: 'Under Review',
                              metric: '${kpi.reviewCount}',
                              subtitle: '${kpi.reviewRate.toStringAsFixed(1)}% rate',
                              accentColor: colors.reviewText,
                              icon: Icons.error_outline_rounded,
                            ),
                          ),
                          const SizedBox(width: AppSpacing.xs),
                          Expanded(
                            child: MetricBento(
                              title: 'Blocked',
                              metric: '${kpi.blockedCount}',
                              subtitle: '${kpi.blockRate.toStringAsFixed(1)}% rate',
                              accentColor: colors.blockText,
                              icon: Icons.gpp_bad_outlined,
                            ),
                          ),
                        ],
                      ),
                    ],
                  );
                }
                return Row(
                  children: [
                    Expanded(
                      child: MetricBento(
                        title: 'Approved',
                        metric: '${kpi.approvedCount}',
                        subtitle: '${kpi.approvalRate.toStringAsFixed(1)}% rate',
                        accentColor: colors.approveText,
                        icon: Icons.check_circle_outline_rounded,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: MetricBento(
                        title: 'Under Review',
                        metric: '${kpi.reviewCount}',
                        subtitle: '${kpi.reviewRate.toStringAsFixed(1)}% rate',
                        accentColor: colors.reviewText,
                        icon: Icons.error_outline_rounded,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: MetricBento(
                        title: 'Blocked',
                        metric: '${kpi.blockedCount}',
                        subtitle: '${kpi.blockRate.toStringAsFixed(1)}% rate',
                        accentColor: colors.blockText,
                        icon: Icons.gpp_bad_outlined,
                      ),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: AppSpacing.md),

            // Risk Distribution Segmented Bar Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          'Risk Distribution Ratio',
                          style: theme.textTheme.titleSmall,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Text(
                        'Avg Score: ${kpi.averageRiskScore} / 100',
                        style: AppTypography.monospaceData(
                          context: context,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: colors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: SizedBox(
                      height: 10,
                      child: Row(
                        children: [
                          Flexible(
                            flex: (kpi.approvalRate * 10).round(),
                            child: Container(color: colors.approveText),
                          ),
                          Flexible(
                            flex: (kpi.reviewRate * 10).round(),
                            child: Container(color: colors.reviewText),
                          ),
                          Flexible(
                            flex: (kpi.blockRate * 10).round().clamp(1, 100),
                            child: Container(color: colors.blockText),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Wrap(
                    spacing: AppSpacing.sm,
                    runSpacing: AppSpacing.xxs,
                    alignment: WrapAlignment.spaceBetween,
                    children: [
                      _buildLegend(
                        label: 'Low (${kpi.approvalRate.toStringAsFixed(1)}%)',
                        color: colors.approveText,
                      ),
                      _buildLegend(
                        label: 'Medium (${kpi.reviewRate.toStringAsFixed(1)}%)',
                        color: colors.reviewText,
                      ),
                      _buildLegend(
                        label: 'High (${kpi.blockRate.toStringAsFixed(1)}%)',
                        color: colors.blockText,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Role-Specific Action Bar
            if (activeRole == DemoRole.merchant) ...[
              AppButton(
                label: 'Simulate New Transaction (Demo Submit)',
                icon: Icons.add_circle_outline_rounded,
                onPressed: () => _showSimulateDialog(context, ref),
              ),
              const SizedBox(height: AppSpacing.md),
            ] else if (activeRole == DemoRole.analyst) ...[
              AppButton(
                label: 'Inspect Review Queue (${kpi.reviewCount} pending)',
                variant: AppButtonVariant.primary,
                icon: Icons.shield_outlined,
                onPressed: () => context.go('/review'),
              ),
              const SizedBox(height: AppSpacing.md),
            ] else ...[
              // Admin view: Active threshold overview
              AppCard(
                padding: AppSpacing.cardPadding,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Active Risk Threshold Rules', style: theme.textTheme.titleSmall),
                    const SizedBox(height: AppSpacing.xs),
                    _buildThresholdRow('Approve Zone', '0 – 39', colors.approveText),
                    const Divider(height: 12),
                    _buildThresholdRow('Manual Review Zone', '40 – 74', colors.reviewText),
                    const Divider(height: 12),
                    _buildThresholdRow('Automated Block Zone', '75 – 100', colors.blockText),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.md),
            ],

            // Recent High-Signal Activity
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Recent Transactions',
                  style: theme.textTheme.titleMedium,
                ),
                TextButton(
                  onPressed: () => context.go('/transactions'),
                  child: Text(
                    'View All (${kpi.totalCount})',
                    style: TextStyle(fontSize: 12, color: colors.brandAccent),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xxs),

            for (final tx in recentTransactions) ...[
              _buildTransactionTile(context, tx, colors),
              const SizedBox(height: AppSpacing.xs),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLegend({required String label, required Color color}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: color),
        ),
      ],
    );
  }

  Widget _buildThresholdRow(String name, String range, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(name, style: const TextStyle(fontSize: 12)),
        Text(
          'Score $range',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: color,
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  Widget _buildTransactionTile(
    BuildContext context,
    Transaction tx,
    AppCustomColors colors,
  ) {
    return AppCard(
      padding: AppSpacing.compactPadding,
      onTap: () => context.push('/transactions/${tx.id}'),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.xs),
            decoration: BoxDecoration(
              color: colors.surfaceSecondary,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              tx.recommendedAction == RiskAction.block
                  ? Icons.gpp_bad_outlined
                  : tx.recommendedAction == RiskAction.review
                      ? Icons.error_outline_rounded
                      : Icons.check_circle_outline_rounded,
              size: 20,
              color: tx.recommendedAction == RiskAction.block
                  ? colors.blockText
                  : tx.recommendedAction == RiskAction.review
                      ? colors.reviewText
                      : colors.approveText,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tx.merchantName,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  '${tx.merchantCategory} • ${DateFormatter.relativeTime(tx.timestamp)}',
                  style: TextStyle(fontSize: 11, color: colors.textSecondary),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.xs),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                CurrencyFormatter.formatBdt(tx.amount),
                style: AppTypography.monospaceData(
                  context: context,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 2),
              RiskBadge(action: tx.recommendedAction, isCompact: true),
            ],
          ),
        ],
      ),
    );
  }

  void _showSimulateDialog(BuildContext context, WidgetRef ref) {
    final amountController = TextEditingController(text: '7500.00');
    int selectedScore = 25;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Simulate Transaction'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Submit a simulated payment transaction into local memory.',
                    style: TextStyle(fontSize: 12),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  TextField(
                    controller: amountController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Amount (BDT)',
                      prefixText: '৳ ',
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text('Simulated Risk Score: $selectedScore / 100'),
                  Slider(
                    value: selectedScore.toDouble(),
                    min: 0,
                    max: 100,
                    divisions: 100,
                    label: '$selectedScore',
                    onChanged: (val) {
                      setDialogState(() => selectedScore = val.round());
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () {
                    final amount = double.tryParse(amountController.text) ?? 5000.0;
                    final newTx = Transaction(
                      id: 'tx_demo_${DateTime.now().millisecondsSinceEpoch}',
                      amount: amount,
                      merchantName: 'TechPulse Gadgets Ltd',
                      merchantCategory: 'Electronics',
                      riskScore: selectedScore,
                      riskFactors: selectedScore > 74
                          ? ['HIGH_AMOUNT', 'NEW_DEVICE']
                          : selectedScore > 39
                              ? ['VELOCITY_WARN']
                              : [],
                      deviceModel: 'Demo Mobile Device',
                      isNewDevice: selectedScore > 74,
                      location: 'Dhaka',
                      transactionsLastHour: 1,
                      previousChargebacks: 0,
                      timestamp: DateTime.now(),
                    );
                    ref.read(transactionsProvider.notifier).addSimulatedTransaction(newTx);
                    Navigator.of(ctx).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Added simulated transaction (Score $selectedScore).'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                  child: const Text('Submit'),
                ),
              ],
            );
          },
        );
      },
    );
  }
}
