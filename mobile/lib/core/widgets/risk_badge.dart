import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';
import '../config/app_risk_constants.dart';

class RiskBadge extends StatelessWidget {
  final RiskAction action;
  final bool isCompact;

  const RiskBadge({
    super.key,
    required this.action,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;

    Color bg;
    Color border;
    Color text;
    String label;
    IconData icon;

    switch (action) {
      case RiskAction.approve:
        bg = colors.approveBg;
        border = colors.approveBorder;
        text = colors.approveText;
        label = 'APPROVE';
        icon = Icons.check_circle_outline_rounded;
        break;
      case RiskAction.review:
        bg = colors.reviewBg;
        border = colors.reviewBorder;
        text = colors.reviewText;
        label = 'REVIEW';
        icon = Icons.error_outline_rounded;
        break;
      case RiskAction.block:
        bg = colors.blockBg;
        border = colors.blockBorder;
        text = colors.blockText;
        label = 'BLOCK';
        icon = Icons.gpp_bad_outlined;
        break;
    }

    return Semantics(
      container: true,
      label: 'Risk decision: $label',
      child: ExcludeSemantics(
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: isCompact ? AppSpacing.xs : AppSpacing.sm,
            vertical: isCompact ? 2 : AppSpacing.xxs,
          ),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: AppSpacing.roundedBadge,
            border: Border.all(color: border, width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(icon, size: isCompact ? 12 : 14, color: text),
              const SizedBox(width: AppSpacing.xxs),
              Text(
                label,
                style: TextStyle(
                  color: text,
                  fontSize: isCompact ? 10 : 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
