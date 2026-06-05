import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/shared_expense_provider.dart';
import '../widgets/shared_expense_tile.dart';
import '../../../core/utils/formatters.dart';

class SharedExpenseListScreen extends ConsumerWidget {
  const SharedExpenseListScreen({super.key});

  static const _months = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expensesAsync = ref.watch(sharedExpenseListProvider);
    final notifier = ref.read(sharedExpenseListProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gastos compartidos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.group),
            tooltip: 'Miembros del hogar',
            onPressed: () => context.push('/shared-expenses/members'),
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/shared-expenses/new'),
          ),
        ],
      ),
      body: expensesAsync.when(
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
        data: (expenses) => RefreshIndicator(
          onRefresh: notifier.reload,
          child: _SharedExpenseContent(
            expenses: expenses,
            notifier: notifier,
            months: _months,
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/shared-expenses/new'),
        backgroundColor: const Color(0xFF0d6efd),
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _SharedExpenseContent extends StatelessWidget {
  final List<dynamic> expenses;
  final SharedExpenseListNotifier notifier;
  final List<String> months;

  const _SharedExpenseContent({
    required this.expenses,
    required this.notifier,
    required this.months,
  });

  @override
  Widget build(BuildContext context) {
    // Calcular totales por persona
    double myTotal = 0;
    final memberTotals = <String, double>{};

    for (final e in expenses) {
      final amount = double.tryParse(e['amount_ars'].toString()) ?? 0;
      final paidBy = e['paid_by_name'] as String?;
      if (paidBy == null) {
        myTotal += amount;
      } else {
        memberTotals[paidBy] = (memberTotals[paidBy] ?? 0) + amount;
      }
    }

    final grandTotal = myTotal +
        memberTotals.values.fold(0.0, (a, b) => a + b);

    return Column(
      children: [
        _MonthSelector(notifier: notifier, months: months),
        if (expenses.isNotEmpty) _TotalsCard(
          myTotal: myTotal,
          memberTotals: memberTotals,
          grandTotal: grandTotal,
        ),
        Expanded(
          child: expenses.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.people_outline, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('Sin gastos compartidos este mes',
                          style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : ListView.separated(
                  itemCount: expenses.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 1, indent: 16),
                  itemBuilder: (context, index) {
                    final expense =
                        expenses[index] as Map<String, dynamic>;
                    return SharedExpenseTile(
                      expense: expense,
                      onTap: () => context.push(
                          '/shared-expenses/edit/${expense['id']}',
                          extra: expense),
                      onDelete: () =>
                          _confirmDelete(context, expense, notifier),
                    );
                  },
                ),
        ),
      ],
    );
  }

  void _confirmDelete(
    BuildContext context,
    Map<String, dynamic> expense,
    SharedExpenseListNotifier notifier,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar gasto compartido'),
        content: Text(
          '¿Eliminar "${expense['description'] ?? expense['category_name']}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await notifier.delete(expense['id'] as int);
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }
}

class _TotalsCard extends StatelessWidget {
  final double myTotal;
  final Map<String, double> memberTotals;
  final double grandTotal;

  const _TotalsCard({
    required this.myTotal,
    required this.memberTotals,
    required this.grandTotal,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0d6efd).withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF0d6efd).withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Yo',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
              Text(formatArs(myTotal),
                  style: const TextStyle(
                      fontSize: 13, fontWeight: FontWeight.bold)),
            ],
          ),
          ...memberTotals.entries.map((e) => Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(e.key,
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w500)),
                    Text(formatArs(e.value),
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.bold)),
                  ],
                ),
              )),
          const Divider(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Total',
                  style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.bold)),
              Text(formatArs(grandTotal),
                  style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFF0d6efd))),
            ],
          ),
        ],
      ),
    );
  }
}

class _MonthSelector extends StatelessWidget {
  final SharedExpenseListNotifier notifier;
  final List<String> months;

  const _MonthSelector({required this.notifier, required this.months});

  void _prev() {
    final prev = DateTime(notifier.currentYear, notifier.currentMonth - 1);
    notifier.setMonth(prev.month, prev.year);
  }

  void _next() {
    final now = DateTime.now();
    final next =
        DateTime(notifier.currentYear, notifier.currentMonth + 1);
    if (next.isAfter(DateTime(now.year, now.month))) return;
    notifier.setMonth(next.month, next.year);
  }

  bool get _canGoNext {
    final now = DateTime.now();
    final next =
        DateTime(notifier.currentYear, notifier.currentMonth + 1);
    return !next.isAfter(DateTime(now.year, now.month));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(icon: const Icon(Icons.chevron_left), onPressed: _prev),
          Text(
            '${months[notifier.currentMonth]} ${notifier.currentYear}',
            style: Theme.of(context)
                .textTheme
                .titleSmall
                ?.copyWith(fontWeight: FontWeight.w600),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: _canGoNext ? _next : null,
            color: _canGoNext ? null : Colors.grey[300],
          ),
        ],
      ),
    );
  }
}
