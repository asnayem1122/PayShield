import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';
import '../../app/theme/app_typography.dart';
import 'app_card.dart';

class MetricBento extends StatelessWidget {
  final String title;
  final String metric;
  final String? subtitle;
  final IconData? icon;
  final Color? accentColor;
  final Widget? trailingBadge;

  const MetricBento({
    super.key,
    required this.title,
    required this.metric,
    this.subtitle,
    this.icon,
    this.accentColor,
    this.trailingBadge,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    return AppCard(
      padding: AppSpacing.cardPadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  title,
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: colors.textSecondary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (trailingBadge != null)
                trailingBadge!
              else if (icon != null)
                Icon(icon, size: 16, color: accentColor ?? colors.textTertiary),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            metric,
            style: AppTypography.monospaceData(
              context: context,
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: accentColor ?? colors.textPrimary,
            ),
          ),
          if (subtitle != null) ...[
            const SizedBox(height: AppSpacing.xxs),
            Text(
              subtitle!,
              style: theme.textTheme.bodySmall?.copyWith(
                color: colors.textTertiary,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }
}
