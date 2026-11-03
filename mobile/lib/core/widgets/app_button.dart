import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';

enum AppButtonVariant {
  primary,
  secondary,
  outline,
  danger,
}

class AppButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final IconData? icon;
  final bool isLoading;
  final double? width;

  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.icon,
    this.isLoading = false,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    Color bg;
    Color fg;
    BorderSide border = BorderSide.none;

    switch (variant) {
      case AppButtonVariant.primary:
        bg = isDark ? colors.textPrimary : AppColors.lightTextPrimary;
        fg = isDark ? colors.canvas : Colors.white;
        break;
      case AppButtonVariant.secondary:
        bg = colors.surfaceSecondary;
        fg = colors.textPrimary;
        break;
      case AppButtonVariant.outline:
        bg = Colors.transparent;
        fg = colors.textPrimary;
        border = BorderSide(color: colors.borderSubtle, width: 1);
        break;
      case AppButtonVariant.danger:
        bg = colors.blockBg;
        fg = colors.blockText;
        border = BorderSide(color: colors.blockBorder, width: 1);
        break;
    }

    Widget content = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (isLoading) ...[
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(fg),
            ),
          ),
          const SizedBox(width: AppSpacing.xs),
        ] else if (icon != null) ...[
          Icon(icon, size: 16, color: fg),
          const SizedBox(width: AppSpacing.xs),
        ],
        Flexible(
          child: Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: fg,
            ),
          ),
        ),
      ],
    );

    return SizedBox(
      width: width ?? double.infinity,
      height: 48, // 48dp minimum accessible touch target
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          backgroundColor: bg,
          foregroundColor: fg,
          side: border,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xs),
          shape: const RoundedRectangleBorder(
            borderRadius: AppSpacing.roundedButton,
          ),
          elevation: 0,
        ),
        onPressed: isLoading ? null : onPressed,
        child: content,
      ),
    );
  }
}
