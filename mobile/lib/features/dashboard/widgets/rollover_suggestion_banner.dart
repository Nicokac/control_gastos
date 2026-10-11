import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_radius.dart';
import '../../../core/theme/app_semantic_colors.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/sensitive_text.dart';
import '../../savings/providers/savings_provider.dart';

class RolloverSuggestionBanner extends ConsumerWidget {
  final Map<String, dynamic> suggestion;

  const RolloverSuggestionBanner({super.key, required this.suggestion});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final color = context.semanticColors.savings;
    final periodStart = DateTime.tryParse(suggestion['period_start'] as String);
    final periodLabel = periodStart != null ? _monthYearLabel(periodStart) : '';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(AppRadius.card),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.savings_outlined, size: 20, color: color),
              const SizedBox(width: 8),
              Expanded(
                child: Wrap(
                  children: [
                    Text(
                      'Te sobraron ',
                      style: TextStyle(fontSize: 13, color: color),
                    ),
                    SensitiveText(
                      formatArsString(suggestion['amount'] as String),
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: color,
                      ),
                    ),
                    Text(
                      periodLabel.isEmpty
                          ? ' el período anterior.'
                          : ' en $periodLabel.',
                      style: TextStyle(fontSize: 13, color: color),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => _dismiss(context, ref),
                  style: OutlinedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppRadius.small),
                    ),
                  ),
                  child: const Text('Descartar'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => _chooseSaving(context, ref),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: color,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppRadius.small),
                    ),
                  ),
                  child: const Text('Destinar a una meta'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _monthYearLabel(DateTime date) {
    const months = [
      'enero',
      'febrero',
      'marzo',
      'abril',
      'mayo',
      'junio',
      'julio',
      'agosto',
      'septiembre',
      'octubre',
      'noviembre',
      'diciembre',
    ];
    return '${months[date.month - 1]} ${date.year}';
  }

  Future<void> _dismiss(BuildContext context, WidgetRef ref) async {
    final notifier = ref.read(savingsListProvider.notifier);
    final error = await notifier.dismissRollover(suggestion['id'] as int);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error ?? 'Listo, el sobrante queda disponible para este período.',
        ),
        backgroundColor: error == null
            ? context.semanticColors.success
            : context.semanticColors.danger,
      ),
    );
  }

  Future<void> _chooseSaving(BuildContext context, WidgetRef ref) async {
    List<dynamic> allSavings;
    try {
      allSavings = await ref.read(savingsListProvider.future);
    } catch (_) {
      allSavings = [];
    }
    final activeSavings = allSavings
        .where((s) => s['status'] == 'ACTIVE')
        .toList();

    if (!context.mounted) return;

    if (activeSavings.isEmpty) {
      context.push('/savings/create');
      return;
    }

    int selectedId = activeSavings.first['id'] as int;
    if (activeSavings.length > 1) {
      final chosen = await showDialog<int>(
        context: context,
        builder: (ctx) {
          int tempSelected = selectedId;
          return StatefulBuilder(
            builder: (ctx, setState) => AlertDialog(
              title: const Text('Destinar sobrante'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: activeSavings.map((s) {
                  final id = s['id'] as int;
                  return RadioListTile<int>(
                    title: Text(s['name'] as String),
                    value: id,
                    groupValue: tempSelected,
                    onChanged: (value) => setState(() => tempSelected = value!),
                  );
                }).toList(),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancelar'),
                ),
                TextButton(
                  onPressed: () => Navigator.pop(ctx, tempSelected),
                  child: const Text('Confirmar'),
                ),
              ],
            ),
          );
        },
      );
      if (chosen == null) return;
      selectedId = chosen;
    }

    final notifier = ref.read(savingsListProvider.notifier);
    final error = await notifier.depositRollover(
      suggestion['id'] as int,
      selectedId,
    );
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(error ?? 'Sobrante destinado correctamente.'),
        backgroundColor: error == null
            ? context.semanticColors.success
            : context.semanticColors.danger,
      ),
    );
  }
}
