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
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/risk_badge.dart';
import '../data/mock_transactions.dart';
import '../domain/transaction_model.dart';

class TransactionHistoryScreen extends ConsumerStatefulWidget {
  final bool initialReviewOnly;

  const TransactionHistoryScreen({
    super.key,
    this.initialReviewOnly = false,
  });

  @override
  ConsumerState<TransactionHistoryScreen> createState() => _TransactionHistoryScreenState();
}

class _TransactionHistoryScreenState extends ConsumerState<TransactionHistoryScreen> {
  String _searchQuery = '';
  RiskAction? _filterAction;

  @override
  void initState() {
    super.initState();
    if (widget.initialReviewOnly) {
      _filterAction = RiskAction.review;
    }
  }

  @override
  Widget build(BuildContext context) {
    final transactions = ref.watch(transactionsProvider);
    final role = ref.watch(demoRoleProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    // Filter transactions
    var filtered = transactions;

    // In Merchant role, filter to own store
    if (role == DemoRole.merchant) {
      filtered = filtered
          .where((tx) => tx.merchantName == 'TechPulse Gadgets Ltd')
          .toList();
    }

    // Filter by risk action chip
    if (_filterAction != null) {
      filtered = filtered
          .where((tx) => tx.recommendedAction == _filterAction)
          .toList();
    }

    // Filter by search query
    if (_searchQuery.trim().isNotEmpty) {
      final q = _searchQuery.toLowerCase();
      filtered = filtered.where((tx) {
        return tx.id.toLowerCase().contains(q) ||
            tx.merchantName.toLowerCase().contains(q) ||
            tx.merchantCategory.toLowerCase().contains(q) ||
            tx.amount.toString().contains(q);
      }).toList();
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Header Search & Filter Bar
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: colors.surfacePrimary,
                border: Border(
                  bottom: BorderSide(color: colors.borderSubtle, width: 1),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        widget.initialReviewOnly
                            ? 'Suspicious Review Queue'
                            : role == DemoRole.merchant
                                ? 'Store Transactions'
                                : 'All System Transactions',
                        style: theme.textTheme.titleMedium,
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: colors.surfaceSecondary,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: colors.borderSubtle, width: 1),
                        ),
                        child: Text(
                          '${filtered.length} Records',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            fontFamily: 'monospace',
                            color: colors.textSecondary,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  // Search Input
                  TextField(
                    decoration: InputDecoration(
                      hintText: 'Search by ID, merchant, category...',
                      prefixIcon: const Icon(Icons.search, size: 18),
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.sm,
                        vertical: AppSpacing.xs,
                      ),
                      suffixIcon: _searchQuery.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 16),
                              onPressed: () => setState(() => _searchQuery = ''),
                            )
                          : null,
                    ),
                    onChanged: (val) => setState(() => _searchQuery = val),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  // Filter Chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildFilterChip(
                          label: 'All (${transactions.length})',
                          isSelected: _filterAction == null,
                          onTap: () => setState(() => _filterAction = null),
                          colors: colors,
                        ),
                        const SizedBox(width: AppSpacing.xs),
                        _buildFilterChip(
                          label: 'Approve',
                          isSelected: _filterAction == RiskAction.approve,
                          onTap: () => setState(() => _filterAction = RiskAction.approve),
                          colors: colors,
                          activeColor: colors.approveText,
                        ),
                        const SizedBox(width: AppSpacing.xs),
                        _buildFilterChip(
                          label: 'Review',
                          isSelected: _filterAction == RiskAction.review,
                          onTap: () => setState(() => _filterAction = RiskAction.review),
                          colors: colors,
                          activeColor: colors.reviewText,
                        ),
                        const SizedBox(width: AppSpacing.xs),
                        _buildFilterChip(
                          label: 'Block',
                          isSelected: _filterAction == RiskAction.block,
                          onTap: () => setState(() => _filterAction = RiskAction.block),
                          colors: colors,
                          activeColor: colors.blockText,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Transactions List
            Expanded(
              child: filtered.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.inbox_outlined,
                            size: 40,
                            color: colors.textTertiary,
                          ),
                          const SizedBox(height: AppSpacing.sm),
                          Text(
                            'No matching transactions found.',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: colors.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Try clearing your search query or filters.',
                            style: TextStyle(fontSize: 12, color: colors.textTertiary),
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: AppSpacing.screenPadding,
                      itemCount: filtered.length,
                      separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.xs),
                      itemBuilder: (context, index) {
                        final tx = filtered[index];
                        return _buildTile(context, tx, colors);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip({
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
    required AppCustomColors colors,
    Color? activeColor,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected
              ? (activeColor ?? colors.brandAccent).withValues(alpha: 0.12)
              : colors.surfaceSecondary,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: isSelected ? (activeColor ?? colors.brandAccent) : colors.borderSubtle,
            width: 1,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? (activeColor ?? colors.brandAccent) : colors.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildTile(
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
                if (tx.analystResolution != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    'Resolved: ${tx.analystResolution}',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: tx.analystResolution == 'CONFIRM_FRAUD'
                          ? colors.blockText
                          : colors.approveText,
                    ),
                  ),
                ],
              ],
            ),
          ),
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
}
