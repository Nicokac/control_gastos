import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class BalanceCard extends StatelessWidget {
  final String totalIncome;
  final String totalExpenses;
  final String balance;
  final VoidCallback? onTapIncome;
  final VoidCallback? onTapExpenses;

  const BalanceCard({
    super.key,
    required this.totalIncome,
    required this.totalExpenses,
    required this.balance,
    this.onTapIncome,
    this.onTapExpenses,
  });

  @override
  Widget build(BuildContext context) {
    final balanceValue = double.tryParse(balance) ?? 0;
    final isPositive = balanceValue >= 0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Balance',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              formatArsString(balance),
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: isPositive ? Colors.green[700] : Colors.red[700],
                  ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _StatItem(
                    label: 'Ingresos',
                    amount: formatArsString(totalIncome),
                    color: Colors.green[700]!,
                    icon: Icons.arrow_upward,
                    onTap: onTapIncome,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _StatItem(
                    label: 'Gastos',
                    amount: formatArsString(totalExpenses),
                    color: Colors.red[700]!,
                    icon: Icons.arrow_downward,
                    onTap: onTapExpenses,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String amount;
  final Color color;
  final IconData icon;
  final VoidCallback? onTap;

  const _StatItem({
    required this.label,
    required this.amount,
    required this.color,
    required this.icon,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: onTap != null
              ? Border.all(color: color.withValues(alpha: 0.2))
              : null,
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                  ),
                  Text(
                    amount,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            if (onTap != null)
              Icon(Icons.chevron_right, color: color, size: 16),
          ],
        ),
      ),
    );
  }
}
