import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class IncomeTile extends StatelessWidget {
  final Map<String, dynamic> income;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const IncomeTile({
    super.key,
    required this.income,
    this.onTap,
    this.onDelete,
  });

  Color get _categoryColor {
    final hex = income['category_color'] as String? ?? '#28a745';
    final clean = hex.replaceFirst('#', '');
    return Color(int.parse('FF$clean', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    final amount = double.tryParse(income['amount_ars'].toString()) ?? 0;
    final date = income['date'] as String? ?? '';
    final description = income['description'] as String? ?? '';
    final categoryName = income['category_name'] as String? ?? '';

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: _categoryColor.withValues(alpha: 0.15),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.arrow_upward, color: _categoryColor, size: 18),
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
              color: Colors.green[700],
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
