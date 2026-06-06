import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../expenses/providers/expense_provider.dart';

// Provider de categorías con invalidación
final allCategoriesProvider = FutureProvider<List<dynamic>>((ref) async {
  final repo = ref.read(expenseRepositoryProvider);
  final response = await repo.getCategories();
  return response;
});

class CategoriesScreen extends ConsumerWidget {
  const CategoriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catsAsync = ref.watch(allCategoriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Categorías'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showCreateDialog(context, ref, null),
          ),
        ],
      ),
      body: catsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (cats) => _CategoriesList(cats: cats, ref: ref),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref, Map<String, dynamic>? parentGroup) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _CreateCategorySheet(
        parentGroup: parentGroup,
        onCreated: () => ref.invalidate(allCategoriesProvider),
      ),
    );
  }
}

class _CategoriesList extends StatelessWidget {
  final List<dynamic> cats;
  final WidgetRef ref;

  const _CategoriesList({required this.cats, required this.ref});

  @override
  Widget build(BuildContext context) {
    final expenseGroups =
        cats.where((c) => c['type'] == 'EXPENSE' && c['parent'] == null).toList();
    final incomeGroups =
        cats.where((c) => c['type'] == 'INCOME' && c['parent'] == null).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _SectionHeader(
          title: 'Gastos',
          color: Colors.red[700]!,
          onAdd: () => _showCreate(context, null, 'EXPENSE'),
        ),
        ...expenseGroups.map((group) => _GroupTile(
              group: group,
              subcats: cats
                  .where((c) => c['parent'] == group['id'])
                  .toList(),
              ref: ref,
              onAdd: () => _showCreate(context, group, 'EXPENSE'),
            )),
        const SizedBox(height: 16),
        _SectionHeader(
          title: 'Ingresos',
          color: Colors.green[700]!,
          onAdd: () => _showCreate(context, null, 'INCOME'),
        ),
        ...incomeGroups.map((group) => _GroupTile(
              group: group,
              subcats: cats
                  .where((c) => c['parent'] == group['id'])
                  .toList(),
              ref: ref,
              onAdd: () => _showCreate(context, group, 'INCOME'),
            )),
      ],
    );
  }

  void _showCreate(BuildContext context, Map<String, dynamic>? parent, String type) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _CreateCategorySheet(
        parentGroup: parent,
        forceType: type,
        onCreated: () => ref.invalidate(allCategoriesProvider),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final Color color;
  final VoidCallback onAdd;

  const _SectionHeader(
      {required this.title, required this.color, required this.onAdd});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Container(
            width: 4,
            height: 18,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: color),
            ),
          ),
          TextButton.icon(
            onPressed: onAdd,
            icon: Icon(Icons.add, size: 14, color: color),
            label: Text('Nuevo grupo',
                style: TextStyle(fontSize: 12, color: color)),
            style: TextButton.styleFrom(
              padding: EdgeInsets.zero,
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        ],
      ),
    );
  }
}

class _GroupTile extends StatelessWidget {
  final Map<String, dynamic> group;
  final List<dynamic> subcats;
  final WidgetRef ref;
  final VoidCallback onAdd;

  const _GroupTile({
    required this.group,
    required this.subcats,
    required this.ref,
    required this.onAdd,
  });

  Color get _color {
    final hex = group['color'] as String? ?? '#6c757d';
    return Color(int.parse('FF${hex.replaceFirst('#', '')}', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    final isSystem = group['is_system'] as bool? ?? false;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        leading: CircleAvatar(
          radius: 16,
          backgroundColor: _color.withValues(alpha: 0.15),
          child: Icon(Icons.folder_outlined, size: 16, color: _color),
        ),
        title: Row(
          children: [
            Text(group['name'] as String,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w600)),
            const SizedBox(width: 6),
            if (isSystem)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text('sistema',
                    style:
                        TextStyle(fontSize: 10, color: Colors.grey[600])),
              ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.add, size: 18),
              onPressed: onAdd,
              tooltip: 'Agregar subcategoría',
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
            const Icon(Icons.expand_more),
          ],
        ),
        children: [
          ...subcats.map((sub) => _SubcatTile(subcat: sub, ref: ref)),
          if (subcats.isEmpty)
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 4, 16, 12),
              child: Text('Sin subcategorías',
                  style: TextStyle(color: Colors.grey, fontSize: 12)),
            ),
        ],
      ),
    );
  }
}

class _SubcatTile extends StatelessWidget {
  final Map<String, dynamic> subcat;
  final WidgetRef ref;

  const _SubcatTile({required this.subcat, required this.ref});

  Color get _color {
    final hex = subcat['color'] as String? ?? '#6c757d';
    return Color(int.parse('FF${hex.replaceFirst('#', '')}', radix: 16));
  }

  Future<void> _delete(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar categoría'),
        content: Text('¿Eliminar "${subcat['name']}"?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      final repo = ref.read(expenseRepositoryProvider);
      await repo.deleteCategory(subcat['id'] as int);
      ref.invalidate(allCategoriesProvider);
      ref.invalidate(categoriesProvider);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('No se puede eliminar: tiene gastos asociados'),
            backgroundColor: Colors.red[700],
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isSystem = subcat['is_system'] as bool? ?? false;

    return ListTile(
      dense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      leading: CircleAvatar(
        radius: 12,
        backgroundColor: _color.withValues(alpha: 0.15),
        child: Icon(Icons.label_outline, size: 12, color: _color),
      ),
      title: Text(subcat['name'] as String,
          style: const TextStyle(fontSize: 13)),
      trailing: isSystem
          ? null
          : IconButton(
              icon: Icon(Icons.delete_outline,
                  size: 18, color: Colors.grey[400]),
              onPressed: () => _delete(context),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
    );
  }
}

class _CreateCategorySheet extends ConsumerStatefulWidget {
  final Map<String, dynamic>? parentGroup;
  final String? forceType;
  final VoidCallback onCreated;

  const _CreateCategorySheet({
    this.parentGroup,
    this.forceType,
    required this.onCreated,
  });

  @override
  ConsumerState<_CreateCategorySheet> createState() =>
      _CreateCategorySheetState();
}

class _CreateCategorySheetState extends ConsumerState<_CreateCategorySheet> {
  final _nameCtrl = TextEditingController();
  String _type = 'EXPENSE';
  String _color = '#6c757d';
  bool _loading = false;

  static const _colors = [
    '#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997',
    '#0dcaf0', '#0d6efd', '#6610f2', '#d63384', '#6c757d',
  ];

  @override
  void initState() {
    super.initState();
    if (widget.forceType != null) _type = widget.forceType!;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_nameCtrl.text.trim().isEmpty) return;
    setState(() => _loading = true);

    final data = {
      'name': _nameCtrl.text.trim(),
      'type': _type,
      'color': _color,
      'icon': 'circle',
      if (widget.parentGroup != null) 'parent': widget.parentGroup!['id'],
    };

    try {
      final repo = ref.read(expenseRepositoryProvider);
      await repo.createCategory(data);
      widget.onCreated();
      if (mounted) Navigator.pop(context);
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isSubcat = widget.parentGroup != null;
    final title = isSubcat
        ? 'Nueva subcategoría en "${widget.parentGroup!['name']}"'
        : 'Nuevo grupo de categoría';

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16, right: 16, top: 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          TextField(
            controller: _nameCtrl,
            autofocus: true,
            decoration: const InputDecoration(
              labelText: 'Nombre *',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          if (!isSubcat && widget.forceType == null) ...[
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(
                labelText: 'Tipo',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'EXPENSE', child: Text('Gasto')),
                DropdownMenuItem(value: 'INCOME', child: Text('Ingreso')),
              ],
              onChanged: (v) => setState(() => _type = v ?? 'EXPENSE'),
            ),
            const SizedBox(height: 16),
          ],
          Text('Color',
              style: TextStyle(fontSize: 13, color: Colors.grey[600])),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _colors.map((hex) {
              final c = Color(
                  int.parse('FF${hex.replaceFirst('#', '')}', radix: 16));
              final selected = _color == hex;
              return GestureDetector(
                onTap: () => setState(() => _color = hex),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: c,
                    shape: BoxShape.circle,
                    border: selected
                        ? Border.all(color: Colors.black, width: 3)
                        : null,
                  ),
                  child: selected
                      ? const Icon(Icons.check,
                          color: Colors.white, size: 16)
                      : null,
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: _loading ? null : _submit,
              child: _loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Crear'),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
