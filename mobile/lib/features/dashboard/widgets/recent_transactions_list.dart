import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/utils/formatters.dart';

class RecentTransactionsList extends StatelessWidget {
  final List<dynamic> expenses;
  final List<dynamic> income;

  const RecentTransactionsList({
    super.key,
    required this.expenses,
    required this.income,
  });

  @override
  Widget build(BuildContext context) {
    // Merge y ordenar por fecha desc
    final all = [
      ...expenses.map((e) => _Transaction.fromExpense(e)),
      ...income.map((e) => _Transaction.fromIncome(e)),
    ]..sort((a, b) => b.date.compareTo(a.date));

    final items = all.take(8).toList();

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Últimos movimientos',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (items.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Center(
                  child: Text(
                    'Sin movimientos recientes',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
              )
            else
              ...items.map((t) => _TransactionTile(transaction: t)),
          ],
        ),
      ),
    );
  }
}

class _Transaction {
  final String description;
  final double amount;
  final bool isExpense;
  final DateTime date;
  final String categoryName;
  final Color categoryColor;

  const _Transaction({
    required this.description,
    required this.amount,
    required this.isExpense,
    required this.date,
    required this.categoryName,
    required this.categoryColor,
  });

  factory _Transaction.fromExpense(Map<String, dynamic> e) {
    return _Transaction(
      description: e['description'] as String? ?? '',
      amount: double.tryParse(e['amount_ars'].toString()) ?? 0,
      isExpense: true,
      date: DateTime.tryParse(e['date'] as String? ?? '') ?? DateTime.now(),
      categoryName: e['category__name'] as String? ?? '',
      categoryColor: _parseColor(e['category__color'] as String? ?? '#6c757d'),
    );
  }

  factory _Transaction.fromIncome(Map<String, dynamic> e) {
    return _Transaction(
      description: e['description'] as String? ?? '',
      amount: double.tryParse(e['amount_ars'].toString()) ?? 0,
      isExpense: false,
      date: DateTime.tryParse(e['date'] as String? ?? '') ?? DateTime.now(),
      categoryName: e['category__name'] as String? ?? '',
      categoryColor: _parseColor(e['category__color'] as String? ?? '#28a745'),
    );
  }

  static Color _parseColor(String hex) {
    final clean = hex.replaceFirst('#', '');
    return Color(int.parse('FF$clean', radix: 16));
  }
}

class _TransactionTile extends StatelessWidget {
  final _Transaction transaction;

  const _TransactionTile({required this.transaction});

  String get _formattedDate {
    return DateFormat('dd/MM', 'es').format(transaction.date);
  }

  String get _formattedAmount {
    final formatted = formatArs(transaction.amount);
    return transaction.isExpense ? '-$formatted' : formatted;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: transaction.categoryColor.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(
              transaction.isExpense
                  ? Icons.arrow_downward
                  : Icons.arrow_upward,
              color: transaction.categoryColor,
              size: 18,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction.description.isNotEmpty
                      ? transaction.description
                      : transaction.categoryName,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  transaction.categoryName,
                  style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                _formattedAmount,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: transaction.isExpense
                      ? Colors.red[700]
                      : Colors.green[700],
                ),
              ),
              Text(
                _formattedDate,
                style: TextStyle(fontSize: 11, color: Colors.grey[500]),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
