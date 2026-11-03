import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';
import '../../app/theme/app_typography.dart';
import '../config/app_risk_constants.dart';

class ScoreGauge extends StatelessWidget {
  final int score;
  final bool showLabel;

  const ScoreGauge({
    super.key,
    required this.score,
    this.showLabel = true,
  });

  @override
  Widget build(BuildContext context) {
    AppRiskConstants.validateScore(score);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final level = AppRiskConstants.getLevelForScore(score);

    Color activeColor;
    String levelName;
    switch (level) {
      case RiskLevel.low:
        activeColor = colors.approveText;
        levelName = 'LOW RISK';
        break;
      case RiskLevel.medium:
        activeColor = colors.reviewText;
        levelName = 'MODERATE RISK';
        break;
      case RiskLevel.high:
        activeColor = colors.blockText;
        levelName = 'HIGH RISK';
        break;
    }

    final double progress = score / 100.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (showLabel) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                'Risk Score',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.2,
                ),
              ),
              RichText(
                text: TextSpan(
                  children: [
                    TextSpan(
                      text: '$score',
                      style: AppTypography.monospaceData(
                        context: context,
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: activeColor,
                      ),
                    ),
                    TextSpan(
                      text: ' / 100',
                      style: AppTypography.monospaceData(
                        context: context,
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: colors.textTertiary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
        ],
        // Segmented Track
        Stack(
          children: [
            Container(
              height: 8,
              decoration: BoxDecoration(
                color: colors.surfaceSecondary,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            FractionallySizedBox(
              widthFactor: progress.clamp(0.02, 1.0),
              child: Container(
                height: 8,
                decoration: BoxDecoration(
                  color: activeColor,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ],
        ),
        if (showLabel) ...[
          const SizedBox(height: AppSpacing.xxs),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '0 (Safe)',
                style: TextStyle(
                  fontSize: 10,
                  color: colors.textTertiary,
                ),
              ),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  levelName,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: activeColor,
                    letterSpacing: 0.5,
                  ),
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                '100 (Critical)',
                style: TextStyle(
                  fontSize: 10,
                  color: colors.textTertiary,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
