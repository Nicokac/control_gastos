import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/amounts_visibility_provider.dart';
import '../../../core/theme/app_semantic_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/sensitive_text.dart';

class ProjectionBanner extends ConsumerWidget {
  final String projectedExpense;
  final String projectedBalance;

  const ProjectionBanner({
    super.key,
    required this.projectedExpense,
    required this.projectedBalance,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final amountsHidden = ref.watch(amountsHiddenProvider);
    final balanceValue = double.tryParse(projectedBalance) ?? 0;
    final color = balanceValue >= 0
        ? context.semanticColors.success
        : context.semanticColors.danger;
    // Espacio no separable para que el salto de línea no deje el "$" solo.
    final expense = amountsHidden
        ? '••••••'
        : formatArsString(projectedExpense).replaceAll(' ', ' ');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Icon(Icons.trending_up, size: 16, color: color),
          const SizedBox(width: 8),
          // Un solo texto para que pase a dos líneas con la fuente agrandada (DT-107).
          Expanded(
            child: Text(
              'Proyección al cierre: $expense en gastos',
              style: TextStyle(fontSize: 12, color: color),
            ),
          ),
          const SizedBox(width: 8),
          SensitiveText(
            formatArsString(projectedBalance),
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
