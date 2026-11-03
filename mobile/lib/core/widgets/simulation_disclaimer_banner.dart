import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';

class SimulationDisclaimerBanner extends StatelessWidget {
  final String text;

  const SimulationDisclaimerBanner({
    super.key,
    this.text = 'Simulated Telemetry — For Academic Demonstration Only. No live banking.',
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: colors.surfaceSecondary,
        borderRadius: AppSpacing.roundedCard,
        border: Border.all(color: colors.borderSubtle, width: 1),
      ),
      child: Row(
        children: [
          Icon(
            Icons.info_outline_rounded,
            size: 14,
            color: colors.brandAccent,
          ),
          const SizedBox(width: AppSpacing.xs),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: colors.textSecondary,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
