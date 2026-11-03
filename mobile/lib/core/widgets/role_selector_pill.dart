import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';
import '../role/demo_role.dart';
import 'app_card.dart';

class RoleSelectorPill extends ConsumerWidget {
  const RoleSelectorPill({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentRole = ref.watch(demoRoleProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;

    return InkWell(
      onTap: () => _showRoleDialog(context, ref),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: colors.surfaceSecondary,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: colors.borderSubtle, width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: colors.brandAccent,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: AppSpacing.xs),
            Text(
              currentRole.displayName,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: colors.textPrimary,
              ),
            ),
            const SizedBox(width: 4),
            Icon(
              Icons.keyboard_arrow_down_rounded,
              size: 14,
              color: colors.textSecondary,
            ),
          ],
        ),
      ),
    );
  }

  void _showRoleDialog(BuildContext context, WidgetRef ref) {
    final currentRole = ref.read(demoRoleProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            color: colors.surfacePrimary,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            border: Border(
              top: BorderSide(color: colors.borderSubtle, width: 1),
            ),
          ),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    decoration: BoxDecoration(
                      color: colors.borderSubtle,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Switch Demo Role', style: theme.textTheme.titleMedium),
                    Text(
                      'Simulation Only',
                      style: TextStyle(fontSize: 11, color: colors.textTertiary),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  'Demonstrates role-tailored dashboard views and screen ergonomics.',
                  style: TextStyle(fontSize: 12, color: colors.textSecondary),
                ),
                const SizedBox(height: AppSpacing.md),
                for (final role in DemoRole.values) ...[
                  AppCard(
                    padding: AppSpacing.compactPadding,
                    borderColor: role == currentRole ? colors.brandAccent : colors.borderSubtle,
                    backgroundColor:
                        role == currentRole ? colors.surfaceSecondary : colors.surfacePrimary,
                    onTap: () {
                      ref.read(demoRoleProvider.notifier).setRole(role);
                      Navigator.of(ctx).pop();
                    },
                    child: Row(
                      children: [
                        Icon(
                          role == DemoRole.merchant
                              ? Icons.storefront_outlined
                              : role == DemoRole.analyst
                                  ? Icons.shield_outlined
                                  : Icons.admin_panel_settings_outlined,
                          size: 20,
                          color: role == currentRole ? colors.brandAccent : colors.textSecondary,
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                role.displayName,
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight:
                                      role == currentRole ? FontWeight.w700 : FontWeight.w600,
                                  color: colors.textPrimary,
                                ),
                              ),
                              Text(
                                role.description,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: colors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        if (role == currentRole)
                          Icon(
                            Icons.check_circle_rounded,
                            size: 18,
                            color: colors.brandAccent,
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}
