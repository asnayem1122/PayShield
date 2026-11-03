import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';
import '../../app/theme/theme_controller.dart';
import 'app_card.dart';

class ThemeSelectorSheet extends ConsumerWidget {
  const ThemeSelectorSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const ThemeSelectorSheet(),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentMode = ref.watch(themeControllerProvider);
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

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
                Text(
                  'Theme Appearance',
                  style: theme.textTheme.titleMedium,
                ),
                Text(
                  'Instant Persistence',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colors.textTertiary,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Select preferred visual mode. System mode adapts automatically.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: colors.textSecondary,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            _buildOption(
              context: context,
              title: 'System Default',
              subtitle: 'Follows operating system dark/light configuration',
              icon: Icons.brightness_auto_rounded,
              mode: ThemeMode.system,
              currentMode: currentMode,
              onSelect: () {
                ref.read(themeControllerProvider.notifier).setThemeMode(ThemeMode.system);
                Navigator.of(context).pop();
              },
            ),
            const SizedBox(height: AppSpacing.xs),
            _buildOption(
              context: context,
              title: 'Light Mode',
              subtitle: 'Warm Alabaster (#F8F9FA) high-contrast workspace',
              icon: Icons.light_mode_outlined,
              mode: ThemeMode.light,
              currentMode: currentMode,
              onSelect: () {
                ref.read(themeControllerProvider.notifier).setThemeMode(ThemeMode.light);
                Navigator.of(context).pop();
              },
            ),
            const SizedBox(height: AppSpacing.xs),
            _buildOption(
              context: context,
              title: 'Dark Mode',
              subtitle: 'Obsidian Crypt (#0B0F17) anti-glare dark void',
              icon: Icons.dark_mode_outlined,
              mode: ThemeMode.dark,
              currentMode: currentMode,
              onSelect: () {
                ref.read(themeControllerProvider.notifier).setThemeMode(ThemeMode.dark);
                Navigator.of(context).pop();
              },
            ),
            const SizedBox(height: AppSpacing.md),
          ],
        ),
      ),
    );
  }

  Widget _buildOption({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required ThemeMode mode,
    required ThemeMode currentMode,
    required VoidCallback onSelect,
  }) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final isSelected = mode == currentMode;

    return AppCard(
      padding: AppSpacing.compactPadding,
      borderColor: isSelected ? colors.brandAccent : colors.borderSubtle,
      backgroundColor: isSelected ? colors.surfaceSecondary : colors.surfacePrimary,
      onTap: onSelect,
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.xs),
            decoration: BoxDecoration(
              color: isSelected ? colors.brandAccent.withValues(alpha: 0.15) : colors.surfaceSecondary,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Icon(
              icon,
              size: 20,
              color: isSelected ? colors.brandAccent : colors.textSecondary,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                    color: colors.textPrimary,
                  ),
                ),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 11,
                    color: colors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          if (isSelected)
            Icon(Icons.check_circle_rounded, size: 18, color: colors.brandAccent),
        ],
      ),
    );
  }
}
