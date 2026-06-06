import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/savings_provider.dart';
import 'savings_list_screen.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/empty_state.dart';

class SavingDetailScreen extends ConsumerWidget {
  final Map<String, dynamic> saving;

  const SavingDetailScreen({super.key, required this.saving});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = saving['id'] as int;
    final movementsAsync = ref.watch(savingMovementsProvider(id));
    final color = parseSavingColor(saving['color'] as String?);
    final progress =
        ((saving['progress_percentage'] as num?)?.toDouble() ?? 0) / 100;
    final current =
        double.tryParse(saving['current_amount']?.toString() ?? '') ?? 0;
    final target =
        double.tryParse(saving['target_amount']?.toString() ?? '') ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: Text(saving['name'] as String? ?? 'Meta de ahorro'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(savingMovementsProvider(id)),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.15),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            savingIconFor(saving['icon'] as String?),
                            color: color,
                            size: 22,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '${formatArs(current)} de ${formatArs(target)}',
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        Text(
                          '${(saving['progress_percentage'] as num? ?? 0)}%',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: progress.clamp(0, 1),
                        minHeight: 8,
                        backgroundColor: color.withValues(alpha: 0.1),
                        valueColor: AlwaysStoppedAnimation(color),
                      ),
                    ),
                    if ((saving['description'] as String?)?.isNotEmpty ==
                        true) ...[
                      const SizedBox(height: 12),
                      Text(
                        saving['description'] as String,
                        style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                'Historial de movimientos',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey[600],
                ),
              ),
            ),
            const SizedBox(height: 8),
            movementsAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 32),
                child: Text(
                  'Error cargando movimientos: $e',
                  style: const TextStyle(color: Colors.red, fontSize: 12),
                ),
              ),
              data: (movements) => movements.isEmpty
                  ? const Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: EmptyState(
                        icon: Icons.receipt_long_outlined,
                        title: 'Sin movimientos',
                        subtitle:
                            'Los depósitos y retiros que registres van a aparecer acá',
                      ),
                    )
                  : Column(
                      children: movements
                          .map(
                            (m) => _MovementTile(
                              movement: m as Map<String, dynamic>,
                            ),
                          )
                          .toList(),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MovementTile extends StatelessWidget {
  final Map<String, dynamic> movement;

  const _MovementTile({required this.movement});

  @override
  Widget build(BuildContext context) {
    final isDeposit = movement['type'] == 'DEPOSIT';
    final color = isDeposit ? Colors.green[700]! : Colors.orange[700]!;
    final amount = double.tryParse(movement['amount']?.toString() ?? '') ?? 0;
    final date = DateTime.tryParse(movement['created_at'] as String? ?? '');
    final description = movement['description'] as String?;

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
      leading: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.15),
          shape: BoxShape.circle,
        ),
        child: Icon(
          isDeposit ? Icons.add : Icons.remove,
          color: color,
          size: 18,
        ),
      ),
      title: Text(
        isDeposit ? 'Depósito' : 'Retiro',
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
      ),
      subtitle: Text(
        [
          if (date != null)
            '${date.day.toString().padLeft(2, '0')}/'
                '${date.month.toString().padLeft(2, '0')}/${date.year}',
          if (description != null && description.isNotEmpty) description,
        ].join(' · '),
        style: TextStyle(fontSize: 12, color: Colors.grey[500]),
      ),
      trailing: Text(
        '${isDeposit ? '+' : '-'} ${formatArs(amount)}',
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }
}
