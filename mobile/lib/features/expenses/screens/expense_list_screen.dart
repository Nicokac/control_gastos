import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/expense_provider.dart';
import '../widgets/expense_tile.dart';
import '../../../core/utils/formatters.dart';

class ExpenseListScreen extends ConsumerWidget {
  const ExpenseListScreen({super.key});

  static const _months = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expensesAsync = ref.watch(expenseListProvider);
    final notifier = ref.read(expenseListProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Gastos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/expenses/new'),
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
          child: _ExpenseListContent(
            expenses: expenses,
            notifier: notifier,
            months: _months,
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/expenses/new'),
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _ExpenseListContent extends StatelessWidget {
  final List<dynamic> expenses;
  final ExpenseListNotifier notifier;
  final List<String> months;

  const _ExpenseListContent({
    required this.expenses,
    required this.notifier,
    required this.months,
  });

  double get _total => expenses.fold(
        0,
        (sum, e) => sum + (double.tryParse(e['amount_ars'].toString()) ?? 0),
      );

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _MonthSelector(notifier: notifier, months: months),
        if (expenses.isNotEmpty)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.red.withValues(alpha: 0.05),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${expenses.length} gasto${expenses.length != 1 ? 's' : ''}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
                Text(
                  'Total: ${formatArs(_total)}',
                  style: TextStyle(
                    color: Colors.red[700],
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        Expanded(
          child: expenses.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.receipt_long_outlined,
                          size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('Sin gastos este mes',
                          style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : ListView.separated(
                  itemCount: expenses.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 1, indent: 16),
                  itemBuilder: (context, index) {
                    final expense = expenses[index] as Map<String, dynamic>;
                    return ExpenseTile(
                      expense: expense,
                      onTap: () =>
                          context.push('/expenses/edit/${expense['id']}',
                              extra: expense),
                      onDelete: () => _confirmDelete(context, expense, notifier),
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
    ExpenseListNotifier notifier,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar gasto'),
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

class _MonthSelector extends StatelessWidget {
  final ExpenseListNotifier notifier;
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
          IconButton(
              icon: const Icon(Icons.chevron_left), onPressed: _prev),
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
