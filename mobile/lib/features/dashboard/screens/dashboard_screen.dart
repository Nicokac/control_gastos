import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/dashboard_provider.dart';
import '../widgets/balance_card.dart';
import '../widgets/expense_chart.dart';
import '../widgets/recent_transactions_list.dart';
import '../widgets/pending_recurring_card.dart';

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
      body: dashboardAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
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
          onRefresh: notifier.reload,
          child: _DashboardContent(data: data, notifier: notifier),
        ),
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
    final recentIncome =
        recentTransactions['income'] as List<dynamic>? ?? [];
    final expensesByCategory =
        data['expenses_by_category'] as List<dynamic>? ?? [];
    final pendingRecurring =
        data['pending_recurring'] as List<dynamic>? ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _MonthSelector(
          month: data['month'] as int,
          year: data['year'] as int,
          onChanged: notifier.setMonth,
        ),
        const SizedBox(height: 12),
        BalanceCard(
          totalIncome: data['total_income'] as String,
          totalExpenses: data['total_expenses'] as String,
          balance: data['balance'] as String,
          month: data['month'] as int,
          year: data['year'] as int,
        ),
        const SizedBox(height: 12),
        _QuickActions(),
        const SizedBox(height: 12),
        if (pendingRecurring.isNotEmpty) ...[
          PendingRecurringCard(pending: pendingRecurring),
          const SizedBox(height: 12),
        ],
        ExpenseChart(expensesByCategory: expensesByCategory),
        const SizedBox(height: 12),
        RecentTransactionsList(
          expenses: recentExpenses,
          income: recentIncome,
        ),
        const SizedBox(height: 16),
      ],
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
      '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ];
    return '${months[month]} $year';
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          icon: const Icon(Icons.chevron_left),
          onPressed: _prev,
        ),
        Text(
          _label,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
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

class _QuickActions extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _ActionButton(
          label: 'Gastos',
          icon: Icons.arrow_downward,
          color: Colors.red[700]!,
          onTap: () => context.push('/expenses'),
        ),
        const SizedBox(width: 8),
        _ActionButton(
          label: 'Ingresos',
          icon: Icons.arrow_upward,
          color: Colors.green[700]!,
          onTap: () => context.push('/income'),
        ),
        const SizedBox(width: 8),
        _ActionButton(
          label: 'Compartidos',
          icon: Icons.people,
          color: const Color(0xFF0d6efd),
          onTap: () => context.push('/shared-expenses'),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  const _ActionButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: enabled
                ? color.withValues(alpha: 0.08)
                : Colors.grey.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: enabled
                  ? color.withValues(alpha: 0.25)
                  : Colors.grey.withValues(alpha: 0.15),
            ),
          ),
          child: Column(
            children: [
              Icon(icon, color: enabled ? color : Colors.grey[400], size: 22),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: enabled ? color : Colors.grey[400],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
