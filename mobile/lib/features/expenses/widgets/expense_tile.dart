import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class ExpenseTile extends StatelessWidget {
  final Map<String, dynamic> expense;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const ExpenseTile({
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

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: _categoryColor.withValues(alpha: 0.15),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.arrow_downward, color: _categoryColor, size: 18),
      ),
      title: Text(
        description.isNotEmpty ? description : categoryName,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        '$categoryName · $date',
        style: TextStyle(fontSize: 12, color: Colors.grey[500]),
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
