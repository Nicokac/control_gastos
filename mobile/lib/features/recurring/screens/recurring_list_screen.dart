import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/recurring_provider.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/empty_state.dart';

class RecurringListScreen extends ConsumerWidget {
  const RecurringListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recurringAsync = ref.watch(recurringListProvider);
    final notifier = ref.read(recurringListProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gastos Fijos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/recurring/new'),
          ),
        ],
      ),
      body: recurringAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              Text(e.toString(),
                  style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 16),
              ElevatedButton(
                  onPressed: notifier.reload, child: const Text('Reintentar')),
            ],
          ),
        ),
        data: (items) => RefreshIndicator(
          onRefresh: notifier.reload,
          child: items.isEmpty
              ? EmptyState(
                  icon: Icons.repeat,
                  title: 'Sin gastos fijos',
                  subtitle: 'Registrá tus gastos recurrentes para llevar el seguimiento',
                  actionLabel: 'Agregar gasto fijo',
                  onAction: () => context.push('/recurring/new'),
                  color: Colors.orange[700],
                )
              : _RecurringContent(items: items, notifier: notifier),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/recurring/new'),
        backgroundColor: Colors.orange[700],
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _RecurringContent extends StatelessWidget {
  final List<dynamic> items;
  final RecurringListNotifier notifier;

  const _RecurringContent({required this.items, required this.notifier});

  @override
  Widget build(BuildContext context) {
    final active = items.where((r) => r['is_active'] == true).toList();
    final inactive = items.where((r) => r['is_active'] == false).toList();

    return ListView(
      children: [
        if (active.isNotEmpty) ...[
          _SectionLabel('Activos (${active.length})'),
          ...active.map((r) => _RecurringTile(
                item: r,
                notifier: notifier,
                onEdit: () => context.push(
                    '/recurring/edit/${r['id']}',
                    extra: r),
              )),
        ],
        if (inactive.isNotEmpty) ...[
          _SectionLabel('Inactivos (${inactive.length})'),
          ...inactive.map((r) => _RecurringTile(
                item: r,
                notifier: notifier,
                onEdit: () => context.push(
                    '/recurring/edit/${r['id']}',
                    extra: r),
              )),
        ],
      ],
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: Colors.grey[500],
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _RecurringTile extends StatelessWidget {
  final Map<String, dynamic> item;
  final RecurringListNotifier notifier;
  final VoidCallback onEdit;

  const _RecurringTile({
    required this.item,
    required this.notifier,
    required this.onEdit,
  });

  Color get _statusColor {
    switch (item['status'] as String? ?? '') {
      case 'paid':
        return Colors.green[700]!;
      case 'overdue':
        return Colors.red[700]!;
      default:
        return Colors.orange[700]!;
    }
  }

  String get _statusLabel {
    switch (item['status'] as String? ?? '') {
      case 'paid':
        return 'Pagado';
      case 'overdue':
        return 'Vencido';
      default:
        return 'Pendiente';
    }
  }

  Color get _categoryColor {
    final hex = item['category_color'] as String? ?? '#6c757d';
    return Color(int.parse('FF${hex.replaceFirst('#', '')}', radix: 16));
  }

  String get _installmentLabel {
    final total = item['total_installments'] as int?;
    final paid = item['installments_paid'] as int? ?? 0;
    if (total == null) return 'Vence día ${item['due_day']}';
    return 'Cuota ${paid + 1}/$total · día ${item['due_day']}';
  }

  Future<void> _markPaid(BuildContext context) async {
    final amountStr = item['last_expense_amount'] as String?;
    final lastAmount =
        amountStr != null ? double.tryParse(amountStr) : null;

    double? amount = lastAmount;

    if (lastAmount == null) {
      // Pedir monto si no hay historial
      final ctrl = TextEditingController();
      final result = await showDialog<double>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Monto del pago'),
          content: TextField(
            controller: ctrl,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Monto',
              prefixText: '\$ ',
              border: OutlineInputBorder(),
            ),
            autofocus: true,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancelar'),
            ),
            TextButton(
              onPressed: () {
                final v = parseArgentineAmount(ctrl.text);
                if (v != null) Navigator.pop(ctx, v);
              },
              child: const Text('Confirmar'),
            ),
          ],
        ),
      );
      if (result == null) return;
      amount = result;
    } else {
      // Confirmar con monto precompletado
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Registrar pago de "${item['name']}"'),
          content: Text(
              '¿Registrar pago por ${formatArs(lastAmount)}?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Confirmar'),
            ),
          ],
        ),
      );
      if (confirmed != true) return;
    }

    final error = await notifier.markPaid(
        item['id'] as int, amount: amount);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error ?? 'Pago registrado correctamente'),
          backgroundColor:
              error == null ? Colors.green[700] : Colors.red[700],
        ),
      );
    }
  }

  Future<void> _unmarkPaid(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Revertir pago'),
        content: Text(
            '¿Revertir el pago de "${item['name']}" de este mes? El gasto registrado será eliminado.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.orange),
            child: const Text('Revertir'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    final error = await notifier.unmarkPaid(item['id'] as int);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error ?? 'Pago revertido'),
          backgroundColor: error == null ? Colors.orange[700] : Colors.red[700],
        ),
      );
    }
  }

  Future<void> _confirmDelete(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar gasto fijo'),
        content: Text('¿Eliminar "${item['name']}"?'),
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
    final isPaid = item['status'] == 'paid';
    final isActive = item['is_active'] as bool? ?? true;

    return ListTile(
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: _categoryColor.withValues(alpha: 0.15),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.repeat, color: _categoryColor, size: 18),
      ),
      title: Text(
        item['name'] as String? ?? '',
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          color: isActive ? null : Colors.grey,
        ),
      ),
      subtitle: Text(
        _installmentLabel,
        style: TextStyle(fontSize: 12, color: Colors.grey[500]),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (item['last_expense_amount'] != null)
                Text(
                  formatArs(double.tryParse(
                          item['last_expense_amount'] as String) ??
                      0),
                  style: const TextStyle(
                      fontSize: 13, fontWeight: FontWeight.bold),
                ),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: _statusColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _statusLabel,
                  style: TextStyle(
                      fontSize: 10,
                      color: _statusColor,
                      fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(width: 8),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, size: 18),
            onSelected: (v) {
              if (v == 'pay') _markPaid(context);
              if (v == 'unmark') _unmarkPaid(context);
              if (v == 'edit') onEdit();
              if (v == 'delete') _confirmDelete(context);
            },
            itemBuilder: (ctx) => [
              if (isActive && !isPaid)
                const PopupMenuItem(
                  value: 'pay',
                  child: ListTile(
                    dense: true,
                    leading: Icon(Icons.check_circle_outline,
                        color: Colors.green),
                    title: Text('Marcar pagado'),
                  ),
                ),
              if (isPaid)
                const PopupMenuItem(
                  value: 'unmark',
                  child: ListTile(
                    dense: true,
                    leading: Icon(Icons.undo, color: Colors.orange),
                    title: Text('Revertir pago',
                        style: TextStyle(color: Colors.orange)),
                  ),
                ),
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
                  leading: Icon(Icons.delete_outline, color: Colors.red),
                  title:
                      Text('Eliminar', style: TextStyle(color: Colors.red)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
