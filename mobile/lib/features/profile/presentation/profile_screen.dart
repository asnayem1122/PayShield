import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../app/theme/theme_controller.dart';
import '../../../core/role/demo_role.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/theme_selector_sheet.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);
    final activeRole = ref.watch(demoRoleProvider);
    final currentTheme = ref.watch(themeControllerProvider);

    String themeLabel;
    switch (currentTheme) {
      case ThemeMode.light:
        themeLabel = 'Light Mode (Warm Alabaster)';
        break;
      case ThemeMode.dark:
        themeLabel = 'Dark Mode (Obsidian Crypt)';
        break;
      case ThemeMode.system:
        themeLabel = 'System Default (Auto)';
        break;
    }

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: AppSpacing.screenPadding,
          children: [
            Text('Settings & Identity', style: theme.textTheme.headlineSmall),
            Text(
              'Environment Preferences & Role Context',
              style: TextStyle(fontSize: 12, color: colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.md),

            // Active Identity Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.sm),
                        decoration: BoxDecoration(
                          color: colors.brandAccent.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          activeRole == DemoRole.merchant
                              ? Icons.storefront_rounded
                              : activeRole == DemoRole.analyst
                                  ? Icons.shield_rounded
                                  : Icons.admin_panel_settings_rounded,
                          size: 24,
                          color: colors.brandAccent,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              activeRole.displayName,
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                            ),
                            Text(
                              activeRole == DemoRole.merchant
                                  ? 'merchant@techpulse.bd'
                                  : activeRole == DemoRole.analyst
                                      ? 'analyst.shafiq@payshield.internal'
                                      : 'admin.nayem@payshield.internal',
                              style: TextStyle(fontSize: 12, color: colors.textSecondary),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    activeRole.description,
                    style: TextStyle(fontSize: 12, color: colors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Appearance & Theme Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Appearance & Theme', style: theme.textTheme.titleSmall),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'Precision Sentinel supports Light, Dark, and System Default.',
                    style: TextStyle(fontSize: 12, color: colors.textSecondary),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  InkWell(
                    onTap: () => ThemeSelectorSheet.show(context),
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.md,
                        vertical: AppSpacing.sm,
                      ),
                      decoration: BoxDecoration(
                        color: colors.surfaceSecondary,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: colors.borderSubtle, width: 1),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Icon(
                                currentTheme == ThemeMode.dark
                                    ? Icons.dark_mode_outlined
                                    : currentTheme == ThemeMode.light
                                        ? Icons.light_mode_outlined
                                        : Icons.brightness_auto_outlined,
                                size: 18,
                                color: colors.brandAccent,
                              ),
                              const SizedBox(width: AppSpacing.sm),
                              Text(
                                themeLabel,
                                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                          Icon(Icons.chevron_right_rounded, size: 18, color: colors.textTertiary),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Disclaimers & Defense Information
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Prototype Governance & Disclaimers', style: theme.textTheme.titleSmall),
                  const SizedBox(height: AppSpacing.xs),
                  _buildBullet(
                    'Simulated Data Only: No real credit card numbers (PAN), CVVs, PINs, or banking passwords are ever collected.',
                    colors,
                  ),
                  const SizedBox(height: 6),
                  _buildBullet(
                    'Frontend Demonstration: Role filtering demonstrates user-journey ergonomics; real authorization is enforced server-side by FastAPI.',
                    colors,
                  ),
                  const SizedBox(height: 6),
                  _buildBullet(
                    'No PCI DSS Claims: This application is an educational FinTech and cybersecurity prototype.',
                    colors,
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),

            AppButton(
              label: 'Sign Out / Switch Demo Identity',
              variant: AppButtonVariant.outline,
              onPressed: () => context.go('/login'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBullet(String text, AppCustomColors colors) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Container(
            width: 4,
            height: 4,
            decoration: BoxDecoration(
              color: colors.textTertiary,
              shape: BoxShape.circle,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: TextStyle(fontSize: 11, color: colors.textSecondary, height: 1.35),
          ),
        ),
      ],
    );
  }
}
