import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../core/config/app_risk_constants.dart';
import '../../../core/role/demo_role.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_text_field.dart';
import '../../../core/widgets/simulation_disclaimer_banner.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController(text: 'merchant@techpulse.bd');
  final _passwordController = TextEditingController(text: '••••••••••••');

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _selectRole(DemoRole role) {
    ref.read(demoRoleProvider.notifier).setRole(role);
    switch (role) {
      case DemoRole.merchant:
        _emailController.text = 'merchant@techpulse.bd';
        break;
      case DemoRole.analyst:
        _emailController.text = 'analyst.shafiq@payshield.internal';
        break;
      case DemoRole.admin:
        _emailController.text = 'admin.nayem@payshield.internal';
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);
    final activeRole = ref.watch(demoRoleProvider);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: AppSpacing.screenPadding,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // App Brand Mark
                  Center(
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: colors.surfaceSecondary,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: colors.borderSubtle, width: 1),
                      ),
                      child: Icon(
                        Icons.shield_outlined,
                        size: 28,
                        color: colors.brandAccent,
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'PayShield',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    'Transaction Fraud-Risk Monitoring',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: colors.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.lg),

                  const SimulationDisclaimerBanner(),
                  const SizedBox(height: AppSpacing.md),

                  // Login Bento Card
                  AppCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Sign In to Console',
                          style: theme.textTheme.titleMedium,
                        ),
                        const SizedBox(height: AppSpacing.xs),
                        Text(
                          'Choose an identity to preview role-tailored workflows.',
                          style: TextStyle(fontSize: 12, color: colors.textSecondary),
                        ),
                        const SizedBox(height: AppSpacing.md),

                        // Fast Role Switcher (Flexible Wrap to prevent overflow on 320px screens)
                        Text(
                          'Quick Demo Role',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: colors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: AppSpacing.xs),
                        Wrap(
                          spacing: AppSpacing.xs,
                          runSpacing: AppSpacing.xs,
                          children: [
                            for (final role in DemoRole.values)
                              InkWell(
                                onTap: () => _selectRole(role),
                                borderRadius: BorderRadius.circular(6),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: role == activeRole
                                        ? colors.brandAccent.withValues(alpha: 0.12)
                                        : colors.surfaceSecondary,
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(
                                      color: role == activeRole
                                          ? colors.brandAccent
                                          : colors.borderSubtle,
                                      width: 1,
                                    ),
                                  ),
                                  child: Text(
                                    role.displayName,
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: role == activeRole
                                          ? FontWeight.w700
                                          : FontWeight.w500,
                                      color: role == activeRole
                                          ? colors.brandAccent
                                          : colors.textSecondary,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.md),

                        AppTextField(
                          label: 'Account Email',
                          controller: _emailController,
                          prefixIcon: Icons.alternate_email_rounded,
                        ),
                        const SizedBox(height: AppSpacing.sm),

                        AppTextField(
                          label: 'Demonstration Credential',
                          controller: _passwordController,
                          obscureText: true,
                          prefixIcon: Icons.lock_outline_rounded,
                          helperText: 'Simulated field — no real password stored.',
                        ),
                        const SizedBox(height: AppSpacing.lg),

                        AppButton(
                          label: 'Enter As ${activeRole.displayName}',
                          onPressed: () => context.go('/dashboard'),
                        ),
                        const SizedBox(height: AppSpacing.sm),

                        Center(
                          child: Text(
                            AppRiskConstants.roleSecurityDisclaimer,
                            style: TextStyle(
                              fontSize: 10,
                              color: colors.textTertiary,
                              height: 1.3,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: AppSpacing.md),
                  Wrap(
                    alignment: WrapAlignment.center,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(
                        'Want to register a demo store? ',
                        style: TextStyle(fontSize: 13, color: colors.textSecondary),
                      ),
                      GestureDetector(
                        onTap: () => context.push('/register'),
                        child: Text(
                          'Merchant Prototype',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: colors.brandAccent,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
