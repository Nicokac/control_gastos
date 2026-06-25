import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/dashboard_provider.dart';
import '../widgets/balance_card.dart';
import '../widgets/expense_chart.dart';
import '../widgets/recent_transactions_list.dart';
import '../widgets/pending_recurring_card.dart';
import '../widgets/dashboard_skeleton.dart';
import '../widgets/last_updated_label.dart';
import '../../../core/widgets/offline_banner.dart';
import '../../../core/utils/formatters.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).valueOrNull;
    final dashboardAsync = ref.watch(dashboardProvider);
    final notifier = ref.read(dashboardProvider.notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          user != null
              ? 'Hola, ${(user['first_name'] as String?)?.isNotEmpty == true ? user['first_name'] : user['username']}'
              : 'Dashboard',
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Configuración',
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineBanner(),
          Expanded(
            child: dashboardAsync.when(
        loading: () => const DashboardSkeleton(),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              Text(
                'Error al cargar el dashboard',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                e.toString(),
                style: const TextStyle(color: Colors.grey, fontSize: 12),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: notifier.reload,
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () async {
            await notifier.reload();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Datos actualizados'),
                  duration: Duration(seconds: 2),
                ),
              );
            }
          },
          child: _DashboardContent(data: data, notifier: notifier),
        ),
      ),
          ),
        ],
      ),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  final Map<String, dynamic> data;
  final DashboardNotifier notifier;

  const _DashboardContent({required this.data, required this.notifier});

  @override
  Widget build(BuildContext context) {
    final recentTransactions =
        data['recent_transactions'] as Map<String, dynamic>? ?? {};
    final recentExpenses =
        recentTransactions['expenses'] as List<dynamic>? ?? [];
    final recentIncome = recentTransactions['income'] as List<dynamic>? ?? [];
    final expensesByCategory =
        data['expenses_by_category'] as List<dynamic>? ?? [];
    final pendingRecurring = data['pending_recurring'] as List<dynamic>? ?? [];
    final totalRecurring = (data['total_recurring'] as int?) ?? 0;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _MonthSelector(
          month: data['month'] as int,
          year: data['year'] as int,
          onChanged: notifier.setMonth,
        ),
        const SizedBox(height: 4),
        LastUpdatedLabel(lastUpdated: notifier.lastUpdated),
        const SizedBox(height: 12),
        BalanceCard(
          totalIncome: data['total_income'] as String,
          totalExpenses: data['total_expenses'] as String,
          balance: data['balance'] as String,
          onTapIncome: () => context.push('/income'),
          onTapExpenses: () => context.push('/expenses'),
        ),
        if (data['projection_available'] == true) ...[
          const SizedBox(height: 8),
          _ProjectionBanner(
            projectedExpense: data['projected_expense'] as String,
            projectedBalance: data['projected_balance'] as String,
          ),
        ],
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.push('/shared-expenses'),
                icon: const Icon(Icons.people, size: 16),
                label: const Text('Compartidos'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF0d6efd),
                  side: const BorderSide(color: Color(0xFF0d6efd)),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.push('/savings'),
                icon: const Icon(Icons.savings_outlined, size: 16),
                label: const Text('Ahorros'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF28a745),
                  side: const BorderSide(color: Color(0xFF28a745)),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.push('/categories'),
                icon: const Icon(Icons.label_outline, size: 16),
                label: const Text('Categorías'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.grey[700],
                  side: BorderSide(color: Colors.grey[400]!),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (totalRecurring > 0) ...[
          PendingRecurringCard(
            pending: pendingRecurring,
            totalRecurring: totalRecurring,
            onViewAll: () => context.push('/recurring'),
          ),
          const SizedBox(height: 12),
        ],
        if (data['next_month_commitment_available'] == true) ...[
          _NextMonthCommitmentCard(data: data),
          const SizedBox(height: 12),
        ],
        ExpenseChart(expensesByCategory: expensesByCategory),
        const SizedBox(height: 12),
        RecentTransactionsList(expenses: recentExpenses, income: recentIncome),
        const SizedBox(height: 16),
      ],
    );
  }
}

class _ProjectionBanner extends StatelessWidget {
  final String projectedExpense;
  final String projectedBalance;

  const _ProjectionBanner({
    required this.projectedExpense,
    required this.projectedBalance,
  });

  @override
  Widget build(BuildContext context) {
    final balanceValue = double.tryParse(projectedBalance) ?? 0;
    final isPositive = balanceValue >= 0;
    final color = isPositive ? Colors.green[700]! : Colors.red[700]!;

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
          Expanded(
            child: Text(
              'Proyección al cierre: ${formatArsString(projectedExpense)} en gastos',
              style: TextStyle(fontSize: 12, color: color),
            ),
          ),
          Text(
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

class _NextMonthCommitmentCard extends StatelessWidget {
  final Map<String, dynamic> data;

  const _NextMonthCommitmentCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final monthName = data['next_month_name'] as String? ?? '';
    final committedTotal = data['next_month_committed_total'] as String? ?? '0';
    final expectedTotal = data['next_month_expected_total'] as String? ?? '0';
    final freeBalance = data['next_month_free_balance'] as String? ?? '0';
    final items = data['next_month_committed_items'] as List<dynamic>? ?? [];
    final unestimated =
        data['next_month_committed_unestimated'] as List<dynamic>? ?? [];

    final freeBalanceValue = double.tryParse(freeBalance) ?? 0;
    final freeBalanceColor =
        freeBalanceValue >= 0 ? Colors.green[700]! : Colors.red[700]!;

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.event_note, size: 18, color: Colors.grey[700]),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Comprometido — $monthName',
                        style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                      ),
                      Text.rich(
                        TextSpan(
                          children: [
                            TextSpan(
                              text: formatArsString(committedTotal),
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.red,
                              ),
                            ),
                            const TextSpan(text: ' en gastos fijos y cuotas'),
                          ],
                        ),
                        style: const TextStyle(fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text('Ingreso fijo esperado:',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                Text(
                  formatArsString(expectedTotal),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                Text('· Te quedaría:',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                Text(
                  formatArsString(freeBalance),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: freeBalanceColor,
                  ),
                ),
              ],
            ),
            if (items.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: items.map((item) {
                  final map = item as Map<String, dynamic>;
                  return Chip(
                    visualDensity: VisualDensity.compact,
                    label: Text(
                      '${map['name']} — ${formatArsString(map['amount'] as String)}',
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: Colors.grey.withValues(alpha: 0.08),
                  );
                }).toList(),
              ),
            ],
            if (unestimated.isNotEmpty) ...[
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: unestimated.map((rec) {
                  final map = rec as Map<String, dynamic>;
                  return Chip(
                    visualDensity: VisualDensity.compact,
                    avatar: const Icon(Icons.help_outline, size: 14),
                    label: Text(
                      '${map['name']} (sin monto estimado)',
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: Colors.grey.withValues(alpha: 0.05),
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _MonthSelector extends StatelessWidget {
  final int month;
  final int year;
  final Future<void> Function(int month, int year) onChanged;

  const _MonthSelector({
    required this.month,
    required this.year,
    required this.onChanged,
  });

  void _prev() {
    final prev = DateTime(year, month - 1);
    onChanged(prev.month, prev.year);
  }

  void _next() {
    final now = DateTime.now();
    final next = DateTime(year, month + 1);
    if (next.isAfter(DateTime(now.year, now.month))) return;
    onChanged(next.month, next.year);
  }

  bool get _canGoNext {
    final now = DateTime.now();
    final next = DateTime(year, month + 1);
    return !next.isAfter(DateTime(now.year, now.month));
  }

  String get _label {
    final months = [
      '',
      'Enero',
      'Febrero',
      'Marzo',
      'Abril',
      'Mayo',
      'Junio',
      'Julio',
      'Agosto',
      'Septiembre',
      'Octubre',
      'Noviembre',
      'Diciembre',
    ];
    return '${months[month]} $year';
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(icon: const Icon(Icons.chevron_left), onPressed: _prev),
        Text(
          _label,
          style: Theme.of(
            context,
          ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
        ),
        IconButton(
          icon: const Icon(Icons.chevron_right),
          onPressed: _canGoNext ? _next : null,
          color: _canGoNext ? null : Colors.grey[300],
        ),
      ],
    );
  }
}
