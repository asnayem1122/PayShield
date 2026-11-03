import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../app/theme/app_spacing.dart';

/// Bento Container Card with 1px hair-line border and zero drop-shadow.
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? backgroundColor;
  final Color? borderColor;

  const AppCard({
    super.key,
    required this.child,
    this.padding = AppSpacing.cardPadding,
    this.onTap,
    this.backgroundColor,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).extension<AppCustomColors>()!;
    final border = BorderSide(
      color: borderColor ?? colors.borderSubtle,
      width: 1,
    );

    final cardContent = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: backgroundColor ?? colors.surfacePrimary,
        borderRadius: AppSpacing.roundedCard,
        border: Border.fromBorderSide(border),
      ),
      child: child,
    );

    if (onTap != null) {
      return Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppSpacing.roundedCard,
          child: cardContent,
        ),
      );
    }

    return cardContent;
  }
}
