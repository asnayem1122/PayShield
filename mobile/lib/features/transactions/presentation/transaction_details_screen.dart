import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../app/theme/app_typography.dart';
import '../../../core/role/demo_role.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/risk_badge.dart';
import '../../../core/widgets/score_gauge.dart';
import '../../../core/widgets/simulation_disclaimer_banner.dart';
import '../data/mock_transactions.dart';

class TransactionDetailsScreen extends ConsumerStatefulWidget {
  final String transactionId;

  const TransactionDetailsScreen({
    super.key,
    required this.transactionId,
  });

  @override
  ConsumerState<TransactionDetailsScreen> createState() => _TransactionDetailsScreenState();
}

class _TransactionDetailsScreenState extends ConsumerState<TransactionDetailsScreen> {
  final _noteController = TextEditingController();

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final transactions = ref.watch(transactionsProvider);
    final activeRole = ref.watch(demoRoleProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    final tx = transactions.firstWhere(
      (item) => item.id == widget.transactionId,
      orElse: () => transactions.first,
    );

    final isResolved = tx.analystResolution != null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transaction Details'),
      ),
      body: SafeArea(
        child: ListView(
          padding: AppSpacing.screenPadding,
          children: [
            const SimulationDisclaimerBanner(
              text: 'Simulated Forensic View — All scores are synthetic demonstrations.',
            ),
            const SizedBox(height: AppSpacing.md),

            // Header Identification Card
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
                          tx.id,
                          style: AppTypography.monospaceData(
                            context: context,
                            fontSize: 13,
                            color: colors.textSecondary,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      RiskBadge(action: tx.recommendedAction),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    CurrencyFormatter.formatBdt(tx.amount),
                    style: AppTypography.monospaceData(
                      context: context,
                      fontSize: 28,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    'Recorded ${DateFormatter.formatFull(tx.timestamp)}',
                    style: TextStyle(fontSize: 11, color: colors.textTertiary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Risk Score Summary Card with direct link to Risk Indicators
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ScoreGauge(score: tx.riskScore),
                  const SizedBox(height: AppSpacing.md),
                  AppButton(
                    label: 'Inspect Risk Indicators & Factor Weights',
                    variant: AppButtonVariant.outline,
                    icon: Icons.insights_rounded,
                    onPressed: () => context.push('/transactions/${tx.id}/risk'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Store & Counterparty Bento
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Merchant Information', style: theme.textTheme.titleSmall),
                  const SizedBox(height: AppSpacing.sm),
                  _buildDetailRow('Store Name', tx.merchantName, colors),
                  const Divider(height: 16),
                  _buildDetailRow('Category', tx.merchantCategory, colors),
                  const Divider(height: 16),
                  _buildDetailRow('Base Currency', tx.currency, colors),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Forensic Telemetry Signals Grid
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Forensic Signals', style: theme.textTheme.titleSmall),
                      Icon(Icons.fingerprint_rounded, size: 16, color: colors.brandAccent),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _buildDetailRow('Device Model', tx.deviceModel, colors),
                  const Divider(height: 16),
                  _buildDetailRow(
                    'New Device Flag',
                    tx.isNewDevice ? 'YES (High Risk Signal)' : 'NO (Known Device)',
                    colors,
                    valueColor: tx.isNewDevice ? colors.blockText : colors.approveText,
                  ),
                  const Divider(height: 16),
                  _buildDetailRow('Reported Location', tx.location, colors),
                  const Divider(height: 16),
                  _buildDetailRow(
                    '1-Hour Velocity',
                    '${tx.transactionsLastHour} transactions',
                    colors,
                    valueColor: tx.transactionsLastHour > 5
                        ? colors.blockText
                        : colors.textPrimary,
                  ),
                  const Divider(height: 16),
                  _buildDetailRow(
                    'Prior Chargebacks',
                    '${tx.previousChargebacks} on record',
                    colors,
                    valueColor: tx.previousChargebacks > 0
                        ? colors.blockText
                        : colors.approveText,
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Analyst Case Resolution Box (For Analyst & Admin Roles)
            if (activeRole != DemoRole.merchant) ...[
              AppCard(
                padding: AppSpacing.cardPadding,
                borderColor: isResolved ? colors.brandAccent : colors.borderSubtle,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Human Review Action', style: theme.textTheme.titleSmall),
                        if (isResolved)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: colors.brandAccent.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'CASE RESOLVED (LOCAL)',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: colors.brandAccent,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      'Analysts can review telemetry and record an operational outcome in local memory.',
                      style: TextStyle(fontSize: 11, color: colors.textSecondary),
                    ),
                    const SizedBox(height: AppSpacing.sm),

                    if (isResolved) ...[
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.sm),
                        decoration: BoxDecoration(
                          color: colors.surfaceSecondary,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Outcome: ${tx.analystResolution}',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: tx.analystResolution == 'CONFIRM_FRAUD'
                                    ? colors.blockText
                                    : colors.approveText,
                              ),
                            ),
                            if (tx.analystNotes != null) ...[
                              const SizedBox(height: 4),
                              Text(
                                'Note: ${tx.analystNotes}',
                                style: TextStyle(fontSize: 12, color: colors.textSecondary),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ] else ...[
                      TextField(
                        controller: _noteController,
                        decoration: const InputDecoration(
                          hintText: 'Add analyst investigation note (simulated)...',
                          isDense: true,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      LayoutBuilder(
                        builder: (context, constraints) {
                          final buttons = [
                            AppButton(
                              label: 'Mark Legitimate',
                              variant: AppButtonVariant.secondary,
                              onPressed: () {
                                ref.read(transactionsProvider.notifier).resolveCase(
                                      tx.id,
                                      'MARK_LEGITIMATE',
                                      _noteController.text.trim().isEmpty
                                          ? 'Verified customer device via phone contact.'
                                          : _noteController.text.trim(),
                                    );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text('Case marked legitimate (Local Mock State updated).'),
                                    duration: Duration(seconds: 2),
                                  ),
                                );
                              },
                            ),
                            AppButton(
                              label: 'Confirm Fraud',
                              variant: AppButtonVariant.danger,
                              onPressed: () {
                                ref.read(transactionsProvider.notifier).resolveCase(
                                      tx.id,
                                      'CONFIRM_FRAUD',
                                      _noteController.text.trim().isEmpty
                                          ? 'Suspicious device and location discrepancy confirmed.'
                                          : _noteController.text.trim(),
                                    );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text('Case confirmed as fraud (Local Mock State updated).'),
                                    duration: Duration(seconds: 2),
                                  ),
                                );
                              },
                            ),
                          ];

                          if (constraints.maxWidth < 260) {
                            return Column(
                              children: [
                                buttons[0],
                                const SizedBox(height: AppSpacing.xs),
                                buttons[1],
                              ],
                            );
                          }

                          return Row(
                            children: [
                              Expanded(child: buttons[0]),
                              const SizedBox(width: AppSpacing.sm),
                              Expanded(child: buttons[1]),
                            ],
                          );
                        },
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.md),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(
    String label,
    String value,
    AppCustomColors colors, {
    Color? valueColor,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(fontSize: 12, color: colors.textSecondary),
        ),
        const SizedBox(width: AppSpacing.xs),
        Flexible(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: valueColor ?? colors.textPrimary,
            ),
            textAlign: TextAlign.end,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}
