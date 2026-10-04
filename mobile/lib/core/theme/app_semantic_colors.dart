import 'package:flutter/material.dart';

class AppSemanticColors extends ThemeExtension<AppSemanticColors> {
  const AppSemanticColors({
    required this.expense,
    required this.income,
    required this.savings,
    required this.shared,
    required this.recurring,
    required this.success,
    required this.danger,
    required this.overdue,
    required this.dueSoon,
    required this.onTrack,
  });

  final Color expense;
  final Color income;
  final Color savings;
  final Color shared;
  final Color recurring;
  final Color success;
  final Color danger;
  final Color overdue;
  final Color dueSoon;
  final Color onTrack;

  static const light = AppSemanticColors(
    expense: Color(0xFFdc3545),
    income: Color(0xFF28a745),
    savings: Color(0xFF28a745),
    shared: Color(0xFF0d6efd),
    recurring: Color(0xFFfd7e14),
    success: Color(0xFF28a745),
    danger: Color(0xFFdc3545),
    overdue: Color(0xFFdc3545),
    dueSoon: Color(0xFFfd7e14),
    onTrack: Color(0xFF28a745),
  );

  static const dark = light;

  @override
  AppSemanticColors copyWith({
    Color? expense,
    Color? income,
    Color? savings,
    Color? shared,
    Color? recurring,
    Color? success,
    Color? danger,
    Color? overdue,
    Color? dueSoon,
    Color? onTrack,
  }) {
    return AppSemanticColors(
      expense: expense ?? this.expense,
      income: income ?? this.income,
      savings: savings ?? this.savings,
      shared: shared ?? this.shared,
      recurring: recurring ?? this.recurring,
      success: success ?? this.success,
      danger: danger ?? this.danger,
      overdue: overdue ?? this.overdue,
      dueSoon: dueSoon ?? this.dueSoon,
      onTrack: onTrack ?? this.onTrack,
    );
  }

  @override
  AppSemanticColors lerp(ThemeExtension<AppSemanticColors>? other, double t) {
    if (other is! AppSemanticColors) return this;
    return AppSemanticColors(
      expense: Color.lerp(expense, other.expense, t)!,
      income: Color.lerp(income, other.income, t)!,
      savings: Color.lerp(savings, other.savings, t)!,
      shared: Color.lerp(shared, other.shared, t)!,
      recurring: Color.lerp(recurring, other.recurring, t)!,
      success: Color.lerp(success, other.success, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      overdue: Color.lerp(overdue, other.overdue, t)!,
      dueSoon: Color.lerp(dueSoon, other.dueSoon, t)!,
      onTrack: Color.lerp(onTrack, other.onTrack, t)!,
    );
  }
}

extension AppSemanticColorsX on BuildContext {
  AppSemanticColors get semanticColors =>
      Theme.of(this).extension<AppSemanticColors>()!;
}
