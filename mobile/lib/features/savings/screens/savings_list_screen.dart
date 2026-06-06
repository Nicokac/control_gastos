import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/savings_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/empty_state.dart';

IconData savingIconFor(String? icon) {
  const map = {
    'bi-piggy-bank': Icons.savings,
    'bi-house': Icons.home_outlined,
    'bi-car-front': Icons.directions_car_outlined,
    'bi-airplane': Icons.flight_outlined,
    'bi-shield-check': Icons.shield_outlined,
    'bi-cash-stack': Icons.payments_outlined,
  };
  return map[icon] ?? Icons.savings;
}

Color parseSavingColor(String? hex) {
  final clean = (hex ?? '#28a745').replaceFirst('#', '');
  return Color(int.parse('FF$clean', radix: 16));
}

class SavingsListScreen extends ConsumerWidget {
  const SavingsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final savingsAsync = ref.watch(savingsListProvider);
    final notifier = ref.read(savingsListProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ahorros'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/savings/new'),
          ),
        ],
      ),
      body: savingsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              Text(
                e.toString(),
                style: const TextStyle(color: Colors.grey, fontSize: 12),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: notifier.reload,
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
        data: (items) => RefreshIndicator(
          onRefresh: notifier.reload,
          child: items.isEmpty
              ? EmptyState(
                  icon: Icons.savings_outlined,
                  title: 'Sin metas de ahorro',
                  subtitle:
                      'Creá una meta para empezar a ahorrar con un objetivo claro',
                  actionLabel: 'Nueva meta',
                  onAction: () => context.push('/savings/new'),
                  color: const Color(0xFF28a745),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  itemBuilder: (ctx, i) => _SavingCard(
                    item: items[i] as Map<String, dynamic>,
                    notifier: notifier,
                  ),
                ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/savings/new'),
        backgroundColor: const Color(0xFF28a745),
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _SavingCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final SavingsListNotifier notifier;

  const _SavingCard({required this.item, required this.notifier});

  String get _statusLabel {
    switch (item['status'] as String? ?? '') {
      case 'COMPLETED':
        return 'Completada';
      case 'CANCELLED':
        return 'Cancelada';
      default:
        return 'Activa';
    }
  }

  Color _statusColor(Color baseColor) {
    switch (item['status'] as String? ?? '') {
      case 'COMPLETED':
        return Colors.green[700]!;
      case 'CANCELLED':
        return Colors.grey[600]!;
      default:
        return baseColor;
    }
  }

  Future<void> _showMovementDialog(
    BuildContext context, {
    required bool isDeposit,
  }) async {
    final amountCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isDeposit ? 'Registrar depósito' : 'Registrar retiro'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: amountCtrl,
                autofocus: true,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: 'Monto *',
                  prefixText: '\$ ',
                  border: OutlineInputBorder(),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Ingresá el monto';
                  final parsed = double.tryParse(v.replaceAll(',', '.'));
                  if (parsed == null || parsed <= 0) return 'Monto inválido';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: descCtrl,
                decoration: const InputDecoration(
                  labelText: 'Descripción',
                  border: OutlineInputBorder(),
                ),
                maxLength: 255,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) Navigator.pop(ctx, true);
            },
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );

    if (result != true) return;

    final amount = double.parse(amountCtrl.text.replaceAll(',', '.'));
    final description = descCtrl.text.trim();
    final id = item['id'] as int;

    final error = isDeposit
        ? await notifier.deposit(id, amount, description)
        : await notifier.withdraw(id, amount, description);

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            error ??
                (isDeposit
                    ? 'Depósito registrado correctamente'
                    : 'Retiro registrado correctamente'),
          ),
          backgroundColor: error == null ? Colors.green[700] : Colors.red[700],
        ),
      );
    }
  }

  Future<void> _confirmDelete(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar meta de ahorro'),
        content: Text(
          '¿Eliminar "${item['name']}"? Esta acción no se puede deshacer.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmed == true) await notifier.delete(item['id'] as int);
  }

  @override
  Widget build(BuildContext context) {
    final color = parseSavingColor(item['color'] as String?);
    final statusColor = _statusColor(color);
    final progress =
        ((item['progress_percentage'] as num?)?.toDouble() ?? 0) / 100;
    final isActive = (item['status'] as String? ?? '') == 'ACTIVE';
    final current =
        double.tryParse(item['current_amount']?.toString() ?? '') ?? 0;
    final target =
        double.tryParse(item['target_amount']?.toString() ?? '') ?? 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => context.push('/savings/${item['id']}', extra: item),
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
                      savingIconFor(item['icon'] as String?),
                      color: color,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['name'] as String? ?? '',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Container(
                          margin: const EdgeInsets.only(top: 4),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 1,
                          ),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            _statusLabel,
                            style: TextStyle(
                              fontSize: 10,
                              color: statusColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert, size: 18),
                    onSelected: (v) {
                      if (v == 'deposit')
                        _showMovementDialog(context, isDeposit: true);
                      if (v == 'withdraw')
                        _showMovementDialog(context, isDeposit: false);
                      if (v == 'edit')
                        context.push(
                          '/savings/edit/${item['id']}',
                          extra: item,
                        );
                      if (v == 'delete') _confirmDelete(context);
                    },
                    itemBuilder: (ctx) => [
                      if (isActive) ...[
                        const PopupMenuItem(
                          value: 'deposit',
                          child: ListTile(
                            dense: true,
                            leading: Icon(
                              Icons.add_circle_outline,
                              color: Colors.green,
                            ),
                            title: Text('Depositar'),
                          ),
                        ),
                        const PopupMenuItem(
                          value: 'withdraw',
                          child: ListTile(
                            dense: true,
                            leading: Icon(
                              Icons.remove_circle_outline,
                              color: Colors.orange,
                            ),
                            title: Text('Retirar'),
                          ),
                        ),
                      ],
                      const PopupMenuItem(
                        value: 'edit',
                        child: ListTile(
                          dense: true,
                          leading: Icon(Icons.edit_outlined),
                          title: Text('Editar'),
                        ),
                      ),
                      const PopupMenuItem(
                        value: 'delete',
                        child: ListTile(
                          dense: true,
                          leading: Icon(
                            Icons.delete_outline,
                            color: Colors.red,
                          ),
                          title: Text(
                            'Eliminar',
                            style: TextStyle(color: Colors.red),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 14),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: progress.clamp(0, 1),
                  minHeight: 8,
                  backgroundColor: color.withValues(alpha: 0.1),
                  valueColor: AlwaysStoppedAnimation(color),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${formatArs(current)} de ${formatArs(target)}',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  Text(
                    '${(item['progress_percentage'] as num? ?? 0)}%',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
