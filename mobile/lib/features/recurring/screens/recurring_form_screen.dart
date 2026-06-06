import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/recurring_provider.dart';

class RecurringFormScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? existing;

  const RecurringFormScreen({super.key, this.existing});

  @override
  ConsumerState<RecurringFormScreen> createState() =>
      _RecurringFormScreenState();
}

class _RecurringFormScreenState extends ConsumerState<RecurringFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final _totalInstCtrl = TextEditingController();
  final _startingInstCtrl = TextEditingController();

  int _dueDay = 1;
  int? _categoryId;
  int? _groupId;
  bool _isActive = true;
  bool _hasCuotas = false;
  bool _loading = false;

  bool get _isEditing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _nameCtrl.text = e['name'] as String? ?? '';
      _notesCtrl.text = e['notes'] as String? ?? '';
      _dueDay = e['due_day'] as int? ?? 1;
      _categoryId = e['category'] as int?;
      _isActive = e['is_active'] as bool? ?? true;
      final total = e['total_installments'] as int?;
      if (total != null) {
        _hasCuotas = true;
        _totalInstCtrl.text = total.toString();
        _startingInstCtrl.text =
            (e['starting_installment'] as int? ?? 1).toString();
      }
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _notesCtrl.dispose();
    _totalInstCtrl.dispose();
    _startingInstCtrl.dispose();
    super.dispose();
  }

  void _resolveGroupFromCategories(List<dynamic> cats) {
    if (_categoryId == null || _groupId != null) return;
    final cat = cats.where((c) => c['id'] == _categoryId).firstOrNull;
    if (cat != null && cat['parent'] != null) {
      _groupId = cat['parent'] as int?;
    }
  }

  Future<void> _pickFromBottomSheet({
    required BuildContext context,
    required String title,
    required List<dynamic> items,
    required int? selectedId,
    required ValueChanged<int> onSelected,
  }) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.85,
        expand: false,
        builder: (ctx, scrollCtrl) => Column(
          children: [
            const SizedBox(height: 8),
            Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 12),
            Text(title,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.bold)),
            const Divider(),
            Expanded(
              child: ListView.builder(
                controller: scrollCtrl,
                itemCount: items.length,
                itemBuilder: (ctx, i) {
                  final item = items[i] as Map<String, dynamic>;
                  final id = item['id'] as int;
                  return ListTile(
                    title: Text(item['name'] as String),
                    trailing: id == selectedId
                        ? const Icon(Icons.check, color: Colors.blue)
                        : null,
                    onTap: () {
                      onSelected(id);
                      Navigator.pop(ctx);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_categoryId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Seleccioná una categoría')),
      );
      return;
    }

    setState(() => _loading = true);

    final data = <String, dynamic>{
      'name': _nameCtrl.text.trim(),
      'category': _categoryId,
      'due_day': _dueDay,
      'is_active': _isActive,
      if (_notesCtrl.text.trim().isNotEmpty) 'notes': _notesCtrl.text.trim(),
      if (_hasCuotas && _totalInstCtrl.text.isNotEmpty) ...{
        'total_installments': int.tryParse(_totalInstCtrl.text),
        'starting_installment': int.tryParse(_startingInstCtrl.text) ?? 1,
      },
    };

    final notifier = ref.read(recurringListProvider.notifier);
    bool ok;
    if (_isEditing) {
      ok = await notifier.editRecurring(widget.existing!['id'] as int, data);
    } else {
      ok = await notifier.create(data);
    }

    setState(() => _loading = false);

    if (ok && mounted) {
      context.pop();
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error al guardar')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(recurringCategoriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar gasto fijo' : 'Nuevo gasto fijo'),
        actions: [
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                  child: SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))),
            )
          else
            TextButton(
              onPressed: _submit,
              child: const Text('Guardar',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Nombre
            TextFormField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Nombre *',
                border: OutlineInputBorder(),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Ingresá un nombre' : null,
            ),
            const SizedBox(height: 16),

            // Día de vencimiento
            DropdownButtonFormField<int>(
              value: _dueDay,
              decoration: const InputDecoration(
                labelText: 'Día de vencimiento *',
                border: OutlineInputBorder(),
              ),
              items: List.generate(28, (i) => i + 1)
                  .map((d) => DropdownMenuItem(
                      value: d, child: Text('Día $d')))
                  .toList(),
              onChanged: (v) => setState(() => _dueDay = v ?? 1),
            ),
            const SizedBox(height: 16),

            // Activo
            SwitchListTile(
              value: _isActive,
              onChanged: (v) => setState(() => _isActive = v),
              title: const Text('Activo'),
              subtitle: const Text('Los inactivos no aparecen en el seguimiento'),
              contentPadding: EdgeInsets.zero,
            ),
            const Divider(),

            // Cuotas
            SwitchListTile(
              value: _hasCuotas,
              onChanged: (v) => setState(() => _hasCuotas = v),
              title: const Text('Es en cuotas'),
              contentPadding: EdgeInsets.zero,
            ),
            if (_hasCuotas) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _totalInstCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Total de cuotas',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) {
                        if (!_hasCuotas) return null;
                        if (v == null || v.isEmpty) return 'Requerido';
                        if (int.tryParse(v) == null) return 'Inválido';
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _startingInstCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: '¿En qué cuota estás?',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 16),

            // Notas
            TextFormField(
              controller: _notesCtrl,
              decoration: const InputDecoration(
                labelText: 'Notas',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
              maxLength: 255,
            ),
            const SizedBox(height: 8),

            // Categoría
            categoriesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Text('Error: $e',
                  style: const TextStyle(color: Colors.red)),
              data: (cats) {
                _resolveGroupFromCategories(cats);

                final groups = cats
                    .where((c) =>
                        c['type'] == 'EXPENSE' && c['parent'] == null)
                    .toList();
                final subcats = _groupId == null
                    ? <dynamic>[]
                    : cats.where((c) => c['parent'] == _groupId).toList();

                final groupName = _groupId == null
                    ? null
                    : (groups.firstWhere((g) => g['id'] == _groupId,
                            orElse: () => {})['name'] as String?);
                final catName = _categoryId == null
                    ? null
                    : (cats.firstWhere((c) => c['id'] == _categoryId,
                            orElse: () => {})['name'] as String?);

                return Column(
                  children: [
                    FormField<int>(
                      initialValue: _groupId,
                      validator: (_) => _categoryId == null
                          ? 'Seleccioná una categoría'
                          : null,
                      builder: (field) => InkWell(
                        onTap: () => _pickFromBottomSheet(
                          context: context,
                          title: 'Grupo de categoría',
                          items: groups,
                          selectedId: _groupId,
                          onSelected: (id) => setState(() {
                            _groupId = id;
                            _categoryId = null;
                          }),
                        ),
                        child: InputDecorator(
                          decoration: InputDecoration(
                            labelText: 'Grupo de categoría *',
                            border: const OutlineInputBorder(),
                            errorText: field.errorText,
                            suffixIcon: const Icon(Icons.arrow_drop_down),
                          ),
                          child: Text(
                            groupName ?? 'Seleccioná un grupo',
                            style: TextStyle(
                              color: groupName == null ? Colors.grey[500] : null,
                            ),
                          ),
                        ),
                      ),
                    ),
                    if (_groupId != null) ...[
                      const SizedBox(height: 16),
                      InkWell(
                        onTap: () => _pickFromBottomSheet(
                          context: context,
                          title: 'Categoría',
                          items: subcats,
                          selectedId: _categoryId,
                          onSelected: (id) =>
                              setState(() => _categoryId = id),
                        ),
                        child: InputDecorator(
                          decoration: const InputDecoration(
                            labelText: 'Categoría *',
                            border: OutlineInputBorder(),
                            suffixIcon: Icon(Icons.arrow_drop_down),
                          ),
                          child: Text(
                            catName ?? 'Seleccioná una categoría',
                            style: TextStyle(
                              color: catName == null ? Colors.grey[500] : null,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
