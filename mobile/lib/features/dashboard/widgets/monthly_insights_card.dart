import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/amounts_visibility_provider.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_semantic_colors.dart';

/// Resumen del último período cerrado que arma el backend (DT-056).
class MonthlyInsightsCard extends ConsumerWidget {
  final Map<String, dynamic> insights;

  const MonthlyInsightsCard({super.key, required this.insights});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final amountsHidden = ref.watch(amountsHiddenProvider);
    final label = (insights['label'] as String).toLowerCase();
    final items = (insights['items'] as List<dynamic>).cast<Map<String, dynamic>>();
    final colors = context.semanticColors;

    return Card(
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.card)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb_outline, size: 18, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Tu $label en resumen',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            for (final item in items) ...[
              const SizedBox(height: 10),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  item['tone'] == 'warning'
                      ? Icon(Icons.arrow_circle_up, size: 18, color: colors.danger)
                      : Icon(Icons.check_circle_outline, size: 18, color: colors.success),
                  const SizedBox(width: 8),
                  Expanded(
                    // Espacio no separable para que el salto de línea no deje el "$" solo.
                    child: Text(
                      ((amountsHidden ? item['masked_text'] : item['text']) as String)
                          .replaceAll('\$ ', '\$ '),
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
