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
import '../../auth/presentation/auth_controller.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);
    final activeRole = ref.watch(demoRoleProvider);
    final authState = ref.watch(authControllerProvider);
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

    final userEmail = authState is AuthAuthenticated
        ? authState.user.email
        : (activeRole == DemoRole.merchant
            ? 'merchant@techpulse.bd'
            : activeRole == DemoRole.analyst
                ? 'analyst.shafiq@payshield.internal'
                : 'admin.nayem@payshield.internal');

    final userName = authState is AuthAuthenticated
        ? authState.user.fullName
        : activeRole.displayName;

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
                              userName,
                              style: const TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w700),
                            ),
                            Text(
                              userEmail,
                              style: TextStyle(
                                  fontSize: 12, color: colors.textSecondary),
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

            // Theme Preferences Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Appearance & Theme', style: theme.textTheme.titleSmall),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'Choose between high-contrast Warm Alabaster light mode or Obsidian Crypt dark mode.',
                    style: TextStyle(fontSize: 12, color: colors.textSecondary),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  InkWell(
                    onTap: () => ThemeSelectorSheet.show(context),
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                      decoration: BoxDecoration(
                        color: colors.surfaceSecondary,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: colors.borderSubtle),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            currentTheme == ThemeMode.dark
                                ? Icons.dark_mode_outlined
                                : currentTheme == ThemeMode.light
                                    ? Icons.light_mode_outlined
                                    : Icons.brightness_auto_outlined,
                            size: 20,
                            color: colors.brandAccent,
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              themeLabel,
                              style: const TextStyle(
                                  fontSize: 13, fontWeight: FontWeight.w500),
                            ),
                          ),
                          Icon(Icons.keyboard_arrow_down_rounded,
                              size: 20, color: colors.textSecondary),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Platform Governance & Compliance Card
            AppCard(
              padding: AppSpacing.cardPadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.verified_user_outlined,
                          size: 18, color: colors.brandAccent),
                      const SizedBox(width: AppSpacing.xs),
                      Text('Security & Academic Compliance',
                          style: theme.textTheme.titleSmall),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  _buildBullet(
                    'Simulated Defense Environment: Deterministic synthetic data generated for cybersecurity academic verification.',
                    colors,
                  ),
                  const SizedBox(height: 6),
                  _buildBullet(
                    'Server-Side Authorization: Authenticated via JWT Bearer tokens with server-side Role-Based Access Control.',
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
              onPressed: () async {
                await ref.read(authControllerProvider.notifier).logout();
                if (context.mounted) {
                  context.go('/login');
                }
              },
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
            style: TextStyle(
                fontSize: 11, color: colors.textSecondary, height: 1.35),
          ),
        ),
      ],
    );
  }
}
