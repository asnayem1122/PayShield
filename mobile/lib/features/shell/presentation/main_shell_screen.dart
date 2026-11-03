import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/theme_controller.dart';
import '../../../core/role/demo_role.dart';
import '../../../core/widgets/role_selector_pill.dart';
import '../../../core/widgets/theme_selector_sheet.dart';

class MainShellScreen extends ConsumerWidget {
  final Widget child;

  const MainShellScreen({
    super.key,
    required this.child,
  });

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/transactions')) return 1;
    if (location.startsWith('/review') || location.startsWith('/analytics')) return 2;
    if (location.startsWith('/profile')) return 3;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context, DemoRole role) {
    switch (index) {
      case 0:
        context.go('/dashboard');
        break;
      case 1:
        context.go('/transactions');
        break;
      case 2:
        if (role == DemoRole.merchant) {
          context.go('/analytics');
        } else {
          context.go('/review');
        }
        break;
      case 3:
        context.go('/profile');
        break;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final currentRole = ref.watch(demoRoleProvider);
    final themeMode = ref.watch(themeControllerProvider);
    final selectedIndex = _calculateSelectedIndex(context);

    IconData themeIcon;
    switch (themeMode) {
      case ThemeMode.light:
        themeIcon = Icons.light_mode_outlined;
        break;
      case ThemeMode.dark:
        themeIcon = Icons.dark_mode_outlined;
        break;
      case ThemeMode.system:
        themeIcon = Icons.brightness_auto_outlined;
        break;
    }

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: colors.surfaceSecondary,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: colors.borderSubtle, width: 1),
              ),
              child: Icon(Icons.shield_outlined, size: 18, color: colors.brandAccent),
            ),
            const SizedBox(width: 8),
            const Text('PayShield'),
          ],
        ),
        actions: [
          const RoleSelectorPill(),
          const SizedBox(width: 8),
          IconButton(
            tooltip: 'Change Theme',
            icon: Icon(themeIcon, size: 20),
            onPressed: () => ThemeSelectorSheet.show(context),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(
            top: BorderSide(color: colors.borderSubtle, width: 1),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: selectedIndex,
          onTap: (idx) => _onItemTapped(idx, context, currentRole),
          items: [
            const BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_outlined),
              activeIcon: Icon(Icons.dashboard_rounded),
              label: 'Dashboard',
            ),
            const BottomNavigationBarItem(
              icon: Icon(Icons.receipt_long_outlined),
              activeIcon: Icon(Icons.receipt_long_rounded),
              label: 'Transactions',
            ),
            BottomNavigationBarItem(
              icon: Icon(
                currentRole == DemoRole.merchant
                    ? Icons.analytics_outlined
                    : Icons.fact_check_outlined,
              ),
              activeIcon: Icon(
                currentRole == DemoRole.merchant
                    ? Icons.analytics_rounded
                    : Icons.fact_check_rounded,
              ),
              label: currentRole == DemoRole.merchant ? 'Analytics' : 'Review Queue',
            ),
            const BottomNavigationBarItem(
              icon: Icon(Icons.tune_outlined),
              activeIcon: Icon(Icons.tune_rounded),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}
