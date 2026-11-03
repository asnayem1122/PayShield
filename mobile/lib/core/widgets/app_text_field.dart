import 'package:flutter/material.dart';
import '../../app/theme/app_spacing.dart';

class AppTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final TextInputType? keyboardType;
  final bool obscureText;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final String? helperText;
  final bool readOnly;

  const AppTextField({
    super.key,
    required this.label,
    this.hint,
    this.controller,
    this.onChanged,
    this.validator,
    this.keyboardType,
    this.obscureText = false,
    this.prefixIcon,
    this.suffixIcon,
    this.helperText,
    this.readOnly = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: AppSpacing.xxs),
        TextFormField(
          controller: controller,
          onChanged: onChanged,
          validator: validator,
          keyboardType: keyboardType,
          obscureText: obscureText,
          readOnly: readOnly,
          style: theme.textTheme.bodyLarge,
          decoration: InputDecoration(
            hintText: hint,
            helperText: helperText,
            prefixIcon: prefixIcon != null ? Icon(prefixIcon, size: 18) : null,
            suffixIcon: suffixIcon,
          ),
        ),
      ],
    );
  }
}
