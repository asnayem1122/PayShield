import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../app/theme/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_text_field.dart';
import '../../../core/widgets/simulation_disclaimer_banner.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _storeNameController = TextEditingController(text: 'Padma Crafts & Retail');
  final _contactEmailController = TextEditingController(text: 'store@padmacrafts.demo');
  String _selectedCategory = 'Retail';

  final List<String> _categories = [
    'Retail',
    'Electronics',
    'Fashion',
    'Grocery',
    'Digital Goods',
  ];

  @override
  void dispose() {
    _storeNameController.dispose();
    _contactEmailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Register Demo Store'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: AppSpacing.screenPadding,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SimulationDisclaimerBanner(
                    text: 'Demonstration Prototype: No live accounts, licenses, or passwords collected.',
                  ),
                  const SizedBox(height: AppSpacing.md),

                  AppCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text('Merchant Store Setup', style: theme.textTheme.titleMedium),
                        const SizedBox(height: AppSpacing.xs),
                        Text(
                          'Simulate registering an online seller account on PayShield.',
                          style: TextStyle(fontSize: 12, color: colors.textSecondary),
                        ),
                        const SizedBox(height: AppSpacing.md),

                        AppTextField(
                          label: 'Simulated Store Name',
                          controller: _storeNameController,
                          prefixIcon: Icons.storefront_outlined,
                        ),
                        const SizedBox(height: AppSpacing.sm),

                        AppTextField(
                          label: 'Demo Contact Email',
                          controller: _contactEmailController,
                          prefixIcon: Icons.email_outlined,
                          helperText: 'For simulated webhook alerts only.',
                        ),
                        const SizedBox(height: AppSpacing.sm),

                        Text(
                          'Business Category',
                          style: theme.textTheme.titleSmall,
                        ),
                        const SizedBox(height: AppSpacing.xxs),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                          decoration: BoxDecoration(
                            color: colors.surfaceSecondary,
                            borderRadius: AppSpacing.roundedInput,
                            border: Border.all(color: colors.borderSubtle, width: 1),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: _selectedCategory,
                              isExpanded: true,
                              dropdownColor: colors.surfacePrimary,
                              style: theme.textTheme.bodyLarge,
                              items: _categories.map((cat) {
                                return DropdownMenuItem(
                                  value: cat,
                                  child: Text(cat),
                                );
                              }).toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() => _selectedCategory = val);
                                }
                              },
                            ),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.lg),

                        AppButton(
                          label: 'Create Demonstration Store',
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Demo Store created in local memory.'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                            context.go('/dashboard');
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Center(
                    child: TextButton(
                      onPressed: () => context.pop(),
                      child: Text(
                        'Back to Sign In',
                        style: TextStyle(color: colors.brandAccent),
                      ),
                    ),
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
