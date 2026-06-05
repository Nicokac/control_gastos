import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/income_provider.dart';
import '../widgets/income_tile.dart';
import '../../../core/utils/formatters.dart';

class IncomeListScreen extends ConsumerWidget {
  const IncomeListScreen({super.key});

  static const _months = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final incomeAsync = ref.watch(incomeListProvider);
    final notifier = ref.read(incomeListProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ingresos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => context.push('/income/new'),
          ),
        ],
      ),
      body: incomeAsync.when(
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
        data: (incomeList) => RefreshIndicator(
          onRefresh: notifier.reload,
          child: _IncomeListContent(
            incomeList: incomeList,
            notifier: notifier,
            months: _months,
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/income/new'),
        backgroundColor: Colors.green[700],
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _IncomeListContent extends StatelessWidget {
  final List<dynamic> incomeList;
  final IncomeListNotifier notifier;
  final List<String> months;

  const _IncomeListContent({
    required this.incomeList,
    required this.notifier,
    required this.months,
  });

  double get _total => incomeList.fold(
        0,
        (sum, e) => sum + (double.tryParse(e['amount_ars'].toString()) ?? 0),
      );

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _MonthSelector(notifier: notifier, months: months),
        if (incomeList.isNotEmpty)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.green.withValues(alpha: 0.05),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${incomeList.length} ingreso${incomeList.length != 1 ? 's' : ''}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
                Text(
                  'Total: ${formatArs(_total)}',
                  style: TextStyle(
                    color: Colors.green[700],
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        Expanded(
          child: incomeList.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.savings_outlined, size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('Sin ingresos este mes',
                          style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                )
              : ListView.separated(
                  itemCount: incomeList.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 1, indent: 16),
                  itemBuilder: (context, index) {
                    final item = incomeList[index] as Map<String, dynamic>;
                    return IncomeTile(
                      income: item,
                      onTap: () => context.push('/income/edit/${item['id']}',
                          extra: item),
                      onDelete: () =>
                          _confirmDelete(context, item, notifier),
                    );
                  },
                ),
        ),
      ],
    );
  }

  void _confirmDelete(
    BuildContext context,
    Map<String, dynamic> item,
    IncomeListNotifier notifier,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar ingreso'),
        content: Text(
          '¿Eliminar "${item['description'] ?? item['category_name']}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await notifier.delete(item['id'] as int);
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
  final IncomeListNotifier notifier;
  final List<String> months;

  const _MonthSelector({required this.notifier, required this.months});

  void _prev() {
    final prev = DateTime(notifier.currentYear, notifier.currentMonth - 1);
    notifier.setMonth(prev.month, prev.year);
  }

  void _next() {
    final now = DateTime.now();
    final next = DateTime(notifier.currentYear, notifier.currentMonth + 1);
    if (next.isAfter(DateTime(now.year, now.month))) return;
    notifier.setMonth(next.month, next.year);
  }

  bool get _canGoNext {
    final now = DateTime.now();
    final next = DateTime(notifier.currentYear, notifier.currentMonth + 1);
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
