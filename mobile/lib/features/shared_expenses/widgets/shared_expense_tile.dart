import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class SharedExpenseTile extends StatelessWidget {
  final Map<String, dynamic> expense;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const SharedExpenseTile({
    super.key,
    required this.expense,
    this.onTap,
    this.onDelete,
  });

  Color get _categoryColor {
    final hex = expense['category_color'] as String? ?? '#6c757d';
    final clean = hex.replaceFirst('#', '');
    return Color(int.parse('FF$clean', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    final amount = double.tryParse(expense['amount_ars'].toString()) ?? 0;
    final date = expense['date'] as String? ?? '';
    final description = expense['description'] as String? ?? '';
    final categoryName = expense['category_name'] as String? ?? '';
    final paidByName = expense['paid_by_name'] as String?;
    final paidLabel = paidByName ?? 'Yo';
    final paidByMe = paidByName == null;

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: _categoryColor.withValues(alpha: 0.15),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.people, color: _categoryColor, size: 18),
      ),
      title: Text(
        description.isNotEmpty ? description : categoryName,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Row(
        children: [
          Text(
            '$categoryName · $date',
            style: TextStyle(fontSize: 12, color: Colors.grey[500]),
          ),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: paidByMe
                  ? const Color(0xFF0d6efd).withValues(alpha: 0.1)
                  : Colors.orange.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              paidLabel,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: paidByMe ? const Color(0xFF0d6efd) : Colors.orange[700],
              ),
            ),
          ),
        ],
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            formatArs(amount),
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Colors.red[700],
            ),
          ),
          if (onDelete != null) ...[
            const SizedBox(width: 4),
            IconButton(
              icon: const Icon(Icons.delete_outline, size: 20),
              color: Colors.grey[400],
              onPressed: onDelete,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ],
      ),
      onTap: onTap,
    );
  }
}
