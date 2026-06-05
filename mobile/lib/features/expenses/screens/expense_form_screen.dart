import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/expense_provider.dart';

class ExpenseFormScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? existing;

  const ExpenseFormScreen({super.key, this.existing});

  @override
  ConsumerState<ExpenseFormScreen> createState() => _ExpenseFormScreenState();
}

class _ExpenseFormScreenState extends ConsumerState<ExpenseFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountCtrl = TextEditingController();
  final _descCtrl = TextEditingController();

  DateTime _date = DateTime.now();
  int? _groupId;
  int? _categoryId;
  String _currency = 'ARS';
  String _paymentMethod = '';
  String _expenseType = '';

  bool _loading = false;
  bool get _isEditing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _amountCtrl.text = e['amount']?.toString() ?? '';
      _descCtrl.text = e['description'] as String? ?? '';
      _date = DateTime.tryParse(e['date'] as String? ?? '') ?? DateTime.now();
      _categoryId = e['category'] as int?;
      _currency = e['currency'] as String? ?? 'ARS';
      _paymentMethod = e['payment_method'] as String? ?? '';
      _expenseType = e['expense_type'] as String? ?? '';
      // _groupId se resuelve después de que carguen las categorías
    }
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
      builder: (ctx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.5,
          minChildSize: 0.3,
          maxChildSize: 0.85,
          expand: false,
          builder: (ctx, scrollCtrl) {
            return Column(
              children: [
                const SizedBox(height: 8),
                Container(
                  width: 40,
                  height: 4,
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
                      final isSelected = id == selectedId;
                      return ListTile(
                        title: Text(item['name'] as String),
                        trailing: isSelected
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
            );
          },
        );
      },
    );
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _date = picked);
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

    final data = {
      'amount': double.parse(_amountCtrl.text.replaceAll(',', '.')),
      'currency': _currency,
      'date': _date.toIso8601String().substring(0, 10),
      'description': _descCtrl.text.trim(),
      'category': _categoryId,
      if (_paymentMethod.isNotEmpty) 'payment_method': _paymentMethod,
      if (_expenseType.isNotEmpty) 'expense_type': _expenseType,
    };

    final notifier = ref.read(expenseListProvider.notifier);
    bool ok;
    if (_isEditing) {
      ok = await notifier.editExpense(widget.existing!['id'] as int, data);
    } else {
      ok = await notifier.create(data);
    }

    setState(() => _loading = false);

    if (ok && mounted) {
      context.pop();
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error al guardar el gasto')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(categoriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar gasto' : 'Nuevo gasto'),
        actions: [
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                  child: SizedBox(
                      width: 20,
                      height: 20,
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
            // Monto
            TextFormField(
              controller: _amountCtrl,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Monto *',
                prefixText: '\$ ',
                border: OutlineInputBorder(),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Ingresá el monto';
                if (double.tryParse(v.replaceAll(',', '.')) == null) {
                  return 'Monto inválido';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),

            // Moneda
            DropdownButtonFormField<String>(
              value: _currency,
              decoration: const InputDecoration(
                labelText: 'Moneda',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'ARS', child: Text('Peso Argentino')),
                DropdownMenuItem(
                    value: 'USD', child: Text('Dólar Estadounidense')),
              ],
              onChanged: (v) => setState(() => _currency = v ?? 'ARS'),
            ),
            const SizedBox(height: 16),

            // Fecha
            InkWell(
              onTap: _pickDate,
              child: InputDecorator(
                decoration: const InputDecoration(
                  labelText: 'Fecha',
                  border: OutlineInputBorder(),
                  suffixIcon: Icon(Icons.calendar_today, size: 18),
                ),
                child: Text(
                  '${_date.day.toString().padLeft(2, '0')}/'
                  '${_date.month.toString().padLeft(2, '0')}/'
                  '${_date.year}',
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Descripción
            TextFormField(
              controller: _descCtrl,
              decoration: const InputDecoration(
                labelText: 'Descripción',
                border: OutlineInputBorder(),
              ),
              maxLength: 255,
            ),
            const SizedBox(height: 8),

            // Método de pago
            DropdownButtonFormField<String>(
              value: _paymentMethod.isEmpty ? null : _paymentMethod,
              decoration: const InputDecoration(
                labelText: 'Método de pago',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: null, child: Text('Sin especificar')),
                DropdownMenuItem(value: 'CASH', child: Text('Efectivo')),
                DropdownMenuItem(value: 'DEBIT', child: Text('Débito')),
                DropdownMenuItem(value: 'CREDIT', child: Text('Crédito')),
                DropdownMenuItem(
                    value: 'TRANSFER', child: Text('Transferencia')),
              ],
              onChanged: (v) =>
                  setState(() => _paymentMethod = v ?? ''),
            ),
            const SizedBox(height: 16),

            // Tipo de gasto
            DropdownButtonFormField<String>(
              value: _expenseType.isEmpty ? null : _expenseType,
              decoration: const InputDecoration(
                labelText: 'Tipo de gasto',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: null, child: Text('Sin especificar')),
                DropdownMenuItem(value: 'FIXED', child: Text('Fijo')),
                DropdownMenuItem(value: 'VARIABLE', child: Text('Variable')),
              ],
              onChanged: (v) =>
                  setState(() => _expenseType = v ?? ''),
            ),
            const SizedBox(height: 16),

            // Categoría
            categoriesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Text('Error cargando categorías: $e',
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
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Grupo
                    FormField<int>(
                      initialValue: _groupId,
                      validator: (_) => _categoryId == null
                          ? 'Seleccioná una categoría'
                          : null,
                      builder: (field) => Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          InkWell(
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
                                suffixIcon:
                                    const Icon(Icons.arrow_drop_down),
                              ),
                              child: Text(
                                groupName ?? 'Seleccioná un grupo',
                                style: TextStyle(
                                  color: groupName == null
                                      ? Colors.grey[500]
                                      : null,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_groupId != null) ...[
                      const SizedBox(height: 16),
                      // Subcategoría
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
                              color:
                                  catName == null ? Colors.grey[500] : null,
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
