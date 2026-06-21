import 'package:flutter/material.dart';
import '../../../core/utils/category_icons.dart';

class CategorySelector extends StatelessWidget {
  final List<dynamic> categories;
  final int? selectedId;
  final ValueChanged<int> onSelected;

  const CategorySelector({
    super.key,
    required this.categories,
    required this.selectedId,
    required this.onSelected,
  });

  Color _parseColor(String hex) {
    final clean = hex.replaceFirst('#', '');
    return Color(int.parse('FF$clean', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: 0.85,
      ),
      itemCount: categories.length,
      itemBuilder: (context, index) {
        final cat = categories[index] as Map<String, dynamic>;
        final id = cat['id'] as int;
        final isSelected = id == selectedId;
        final color = _parseColor(cat['color'] as String? ?? '#6c757d');

        return GestureDetector(
          onTap: () => onSelected(id),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            decoration: BoxDecoration(
              color: isSelected
                  ? color.withValues(alpha: 0.2)
                  : Colors.grey.withValues(alpha: 0.07),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isSelected ? color : Colors.transparent,
                width: 2,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _iconFromName(cat['icon'] as String? ?? 'circle'),
                  color: isSelected ? color : Colors.grey[600],
                  size: 22,
                ),
                const SizedBox(height: 4),
                Text(
                  cat['name'] as String? ?? '',
                  style: TextStyle(
                    fontSize: 10,
                    color: isSelected ? color : Colors.grey[700],
                    fontWeight: isSelected
                        ? FontWeight.bold
                        : FontWeight.normal,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  IconData _iconFromName(String name) => categoryIconFromName(name);
}
