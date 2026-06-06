import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class PendingRecurringCard extends StatelessWidget {
  final List<dynamic> pending;
  final int totalRecurring;
  final VoidCallback? onViewAll;

  const PendingRecurringCard({
    super.key,
    required this.pending,
    required this.totalRecurring,
    this.onViewAll,
  });

  @override
  Widget build(BuildContext context) {
    if (pending.isEmpty) return const SizedBox.shrink();

    final overdueCount = pending.where((r) => r['status'] == 'overdue').length;
    final pendingCount = pending.where((r) => r['status'] == 'pending').length;
    final paid = totalRecurring - pending.length;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                const Icon(Icons.warning_amber_rounded,
                    color: Colors.orange, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Gastos fijos',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (onViewAll != null)
                  TextButton(
                    onPressed: onViewAll,
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: const Text('Ver todos'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _SummaryChip(
                  label: '$paid pagados',
                  color: Colors.green[700]!,
                  icon: Icons.check_circle_outline,
                ),
                const SizedBox(width: 8),
                if (pendingCount > 0)
                  _SummaryChip(
                    label: '$pendingCount pendientes',
                    color: Colors.orange[700]!,
                    icon: Icons.schedule,
                  ),
                if (pendingCount > 0 && overdueCount > 0)
                  const SizedBox(width: 8),
                if (overdueCount > 0)
                  _SummaryChip(
                    label: '$overdueCount vencidos',
                    color: Colors.red[700]!,
                    icon: Icons.error_outline,
                  ),
              ],
            ),
            const SizedBox(height: 8),
            _ProgressBar(paid: paid, total: totalRecurring),
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: Text(
                '$paid de $totalRecurring pagados',
                style: TextStyle(fontSize: 11, color: Colors.grey[500]),
              ),
            ),
            if (pending.isNotEmpty) ...[
              const Divider(height: 20),
              ...pending.take(2).map((r) => _RecurringRow(item: r)),
              if (pending.length > 2)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    '+ ${pending.length - 2} más',
                    style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ProgressBar extends StatelessWidget {
  final int paid;
  final int total;
  const _ProgressBar({required this.paid, required this.total});

  @override
  Widget build(BuildContext context) {
    final progress = total > 0 ? paid / total : 0.0;
    return ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: LinearProgressIndicator(
        value: progress,
        minHeight: 6,
        backgroundColor: Colors.grey[200],
        valueColor: AlwaysStoppedAnimation<Color>(Colors.green[600]!),
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  final String label;
  final Color color;
  final IconData icon;
  const _SummaryChip(
      {required this.label, required this.color, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
                fontSize: 11, color: color, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _RecurringRow extends StatelessWidget {
  final Map<String, dynamic> item;
  const _RecurringRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final isOverdue = item['status'] == 'overdue';
    final color = isOverdue ? Colors.red[700]! : Colors.orange[700]!;
    final amount = item['last_amount'] != null
        ? double.tryParse(item['last_amount'] as String)
        : null;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(Icons.repeat, size: 14, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              item['name'] as String? ?? '',
              style: const TextStyle(fontSize: 13),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (amount != null)
            Text(
              formatArs(amount),
              style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: color),
            ),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              isOverdue ? 'Vencido' : 'Pendiente',
              style: TextStyle(
                  fontSize: 10, color: color, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}
