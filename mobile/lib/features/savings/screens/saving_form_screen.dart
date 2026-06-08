import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/savings_provider.dart';
import 'savings_list_screen.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/widgets/section_label.dart';

const _iconChoices = [
  ('bi-piggy-bank', 'Alcancía'),
  ('bi-house', 'Casa'),
  ('bi-car-front', 'Auto'),
  ('bi-airplane', 'Viaje'),
  ('bi-shield-check', 'Emergencias'),
  ('bi-cash-stack', 'General'),
];

class SavingFormScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? existing;

  const SavingFormScreen({super.key, this.existing});

  @override
  ConsumerState<SavingFormScreen> createState() => _SavingFormScreenState();
}

class _SavingFormScreenState extends ConsumerState<SavingFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _targetCtrl = TextEditingController();

  DateTime? _targetDate;
  String _currency = 'ARS';
  String _icon = _iconChoices.first.$1;
  String _color = '#28a745';

  bool _loading = false;
  bool get _isEditing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    if (e != null) {
      _nameCtrl.text = e['name'] as String? ?? '';
      _descCtrl.text = e['description'] as String? ?? '';
      _targetCtrl.text = e['target_amount']?.toString() ?? '';
      _currency = e['currency'] as String? ?? 'ARS';
      _icon = e['icon'] as String? ?? _iconChoices.first.$1;
      _color = e['color'] as String? ?? '#28a745';
      final date = e['target_date'] as String?;
      if (date != null && date.isNotEmpty) {
        _targetDate = DateTime.tryParse(date);
      }
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _descCtrl.dispose();
    _targetCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _targetDate ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime(DateTime.now().year + 20),
    );
    if (picked != null) setState(() => _targetDate = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    final data = <String, dynamic>{
      'name': _nameCtrl.text.trim(),
      'target_amount': parseArgentineAmount(_targetCtrl.text) ?? 0.0,
      'currency': _currency,
      'icon': _icon,
      'color': _color,
      if (_descCtrl.text.trim().isNotEmpty)
        'description': _descCtrl.text.trim(),
      if (_targetDate != null)
        'target_date': _targetDate!.toIso8601String().substring(0, 10),
    };

    final notifier = ref.read(savingsListProvider.notifier);
    bool ok;
    if (_isEditing) {
      ok = await notifier.editSaving(widget.existing!['id'] as int, data);
    } else {
      ok = await notifier.create(data);
    }

    setState(() => _loading = false);

    if (ok && mounted) {
      context.pop();
    } else if (mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Error al guardar la meta')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = parseSavingColor(_color);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Editar meta' : 'Nueva meta de ahorro'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
          children: [
            TextFormField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Nombre *',
                prefixIcon: Icon(Icons.flag_outlined),
                border: OutlineInputBorder(),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Ingresá un nombre' : null,
            ),
            const SizedBox(height: 16),

            TextFormField(
              controller: _targetCtrl,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                labelText: 'Monto objetivo *',
                prefixIcon: const Icon(Icons.flag_circle_outlined),
                prefixText: '\$ ',
                border: const OutlineInputBorder(),
                filled: true,
                fillColor: const Color(0xFF28a745).withValues(alpha: 0.05),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Ingresá el monto objetivo';
                final parsed = parseArgentineAmount(v);
                if (parsed == null || parsed <= 0) return 'Monto inválido';
                return null;
              },
            ),
            const SizedBox(height: 16),

            DropdownButtonFormField<String>(
              value: _currency,
              decoration: const InputDecoration(
                labelText: 'Moneda',
                prefixIcon: Icon(Icons.attach_money),
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'ARS', child: Text('Peso Argentino')),
                DropdownMenuItem(
                  value: 'USD',
                  child: Text('Dólar Estadounidense'),
                ),
              ],
              onChanged: (v) => setState(() => _currency = v ?? 'ARS'),
            ),
            const SizedBox(height: 16),

            InkWell(
              onTap: _pickDate,
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: 'Fecha objetivo',
                  prefixIcon: const Icon(Icons.event_outlined),
                  border: const OutlineInputBorder(),
                  suffixIcon: _targetDate != null
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () => setState(() => _targetDate = null),
                        )
                      : const Icon(Icons.arrow_drop_down),
                ),
                child: Text(
                  _targetDate == null
                      ? 'Sin definir'
                      : '${_targetDate!.day.toString().padLeft(2, '0')}/'
                            '${_targetDate!.month.toString().padLeft(2, '0')}/'
                            '${_targetDate!.year}',
                  style: TextStyle(
                    color: _targetDate == null ? Colors.grey[500] : null,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

            const SectionLabel('Apariencia'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: _iconChoices.map((choice) {
                final selected = _icon == choice.$1;
                return InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => setState(() => _icon = choice.$1),
                  child: Container(
                    width: 72,
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: selected
                          ? color.withValues(alpha: 0.15)
                          : Colors.grey[100],
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: selected ? color : Colors.transparent,
                        width: 2,
                      ),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          savingIconFor(choice.$1),
                          color: selected ? color : Colors.grey[600],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          choice.$2,
                          style: TextStyle(
                            fontSize: 10,
                            color: selected ? color : Colors.grey[600],
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: const [
                '#28a745',
                '#0d6efd',
                '#fd7e14',
                '#dc3545',
                '#6610f2',
                '#20c997',
              ].map((hex) => _colorOption(hex)).toList(),
            ),

            const SizedBox(height: 24),
            const SectionLabel('Detalles opcionales'),
            const SizedBox(height: 8),
            TextFormField(
              controller: _descCtrl,
              decoration: const InputDecoration(
                labelText: 'Descripción',
                prefixIcon: Icon(Icons.notes_outlined),
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
              maxLength: 255,
            ),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.all(16),
        child: FilledButton.icon(
          onPressed: _loading ? null : _submit,
          icon: _loading
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Icon(Icons.check),
          label: Text(_isEditing ? 'Guardar cambios' : 'Crear meta'),
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xFF28a745),
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
    );
  }

  Widget _colorOption(String hex) {
    final color = parseSavingColor(hex);
    final selected = _color == hex;

    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () => setState(() => _color = hex),
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          border: selected ? Border.all(color: Colors.black87, width: 2) : null,
        ),
        child: selected
            ? const Icon(Icons.check, color: Colors.white, size: 18)
            : null,
      ),
    );
  }
}
