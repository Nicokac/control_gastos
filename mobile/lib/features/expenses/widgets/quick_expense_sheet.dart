import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_semantic_colors.dart';
import '../../../data/repositories/expense_repository.dart';
import '../providers/expense_provider.dart';

/// Carga rápida: "15000 super débito" → vista previa → guardar (web 1.32.0).
Future<void> showQuickExpenseSheet(BuildContext context) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (_) => const QuickExpenseSheet(),
  );
}

/// Grupos de gasto con sus subcategorías visibles, en el orden de la API.
List<({Map<String, dynamic> group, List<Map<String, dynamic>> subcategories})>
    groupExpenseCategories(List<dynamic> categories) {
  final cats = categories.cast<Map<String, dynamic>>();
  return [
    for (final group
        in cats.where((c) => c['type'] == 'EXPENSE' && c['parent'] == null))
      (
        group: group,
        subcategories: cats
            .where((c) => c['parent'] == group['id'] && c['is_hidden'] != true)
            .toList(),
      ),
  ].where((g) => g.subcategories.isNotEmpty).toList();
}

/// Texto que explica de dónde salió la categoría sugerida (igual que la web).
String categoryHint(Map<String, dynamic> preview, {required bool suggested}) {
  final hasDescription = (preview['description'] as String? ?? '').isNotEmpty;
  if (!suggested) {
    return 'No pude adivinar la categoría: elegila para guardar.'
        '${hasDescription ? ' La recordamos para la próxima.' : ''}';
  }
  final source = switch (preview['category_source']) {
    'regla' => 'Sugerida por tu regla “${preview['category_rule']}”.',
    'historial' => 'Sugerida por tus gastos anteriores.',
    _ => 'Sugerida por el nombre de la categoría.',
  };
  return hasDescription
      ? '$source Si elegís otra, la recordamos para la próxima.'
      : source;
}

class QuickExpenseSheet extends ConsumerStatefulWidget {
  const QuickExpenseSheet({super.key});

  @override
  ConsumerState<QuickExpenseSheet> createState() => _QuickExpenseSheetState();
}

class _QuickExpenseSheetState extends ConsumerState<QuickExpenseSheet> {
  final _textCtrl = TextEditingController();
  bool _parsing = false;
  bool _saving = false;
  String? _error;
  Map<String, dynamic>? _preview;
  int? _suggestedId;
  int? _categoryId;

  @override
  void dispose() {
    _textCtrl.dispose();
    super.dispose();
  }

  Future<void> _parse() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty || _parsing) return;
    setState(() {
      _parsing = true;
      _error = null;
    });
    try {
      final preview =
          await ref.read(expenseRepositoryProvider).quickParse(text);
      final categories = await ref.read(categoriesProvider.future);
      final visibleIds = groupExpenseCategories(categories)
          .expand((g) => g.subcategories)
          .map((c) => c['id'])
          .toSet();
      final suggested = preview['category_id'] as int?;
      if (!mounted) return;
      setState(() {
        _preview = preview;
        _suggestedId = visibleIds.contains(suggested) ? suggested : null;
        _categoryId = _suggestedId;
      });
    } on QuickEntryException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No pudimos conectar. Probá de nuevo.');
      }
    } finally {
      if (mounted) setState(() => _parsing = false);
    }
  }

  Map<String, dynamic> _expenseData(Map<String, dynamic> preview) {
    final payment = preview['payment_method'] as String? ?? '';
    return {
      'amount': preview['amount'],
      'currency': preview['currency'],
      'exchange_rate': preview['exchange_rate'],
      'date': preview['date'],
      'description': preview['description'] ?? '',
      'category': _categoryId,
      if (payment.isNotEmpty) 'payment_method': payment,
    };
  }

  Future<void> _save() async {
    final preview = _preview;
    if (preview == null || _categoryId == null || _saving) return;
    setState(() => _saving = true);
    final messenger = ScaffoldMessenger.of(context);
    final created = await ref.read(expenseListProvider.notifier).quickCreate({
      ..._expenseData(preview),
      'suggested_category': _suggestedId ?? '',
    });
    if (!mounted) return;
    if (created == null) {
      setState(() {
        _saving = false;
        _error = 'No pudimos guardar el gasto. Probá de nuevo.';
      });
      return;
    }
    Navigator.of(context).pop();
    final label = (preview['description'] as String? ?? '').isNotEmpty
        ? preview['description']
        : created['category_name'];
    final rule = created['learned_rule'] as Map<String, dynamic>?;
    messenger.showSnackBar(
      SnackBar(
        content: Text(
          'Gasto registrado: $label - ${preview['amount_display']}'
          '${rule == null ? '' : '\nDesde ahora, “${rule['pattern']}” se sugiere en ${rule['category_name']}.'}',
        ),
      ),
    );
  }

  void _openFullForm() {
    final preview = _preview!;
    final router = GoRouter.of(context);
    Navigator.of(context).pop();
    router.push('/expenses/new', extra: _expenseData(preview));
  }

  Future<void> _pickCategory(List<dynamic> categories) async {
    final groups = groupExpenseCategories(categories);
    final picked = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (ctx, scrollCtrl) => ListView(
          controller: scrollCtrl,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Categoría',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
            for (final g in groups) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: Text(
                  g.group['name'] as String,
                  style: Theme.of(ctx).textTheme.labelLarge,
                ),
              ),
              for (final sub in g.subcategories)
                ListTile(
                  title: Text(sub['name'] as String),
                  trailing: sub['id'] == _categoryId
                      ? const Icon(Icons.check)
                      : null,
                  onTap: () => Navigator.pop(ctx, sub['id'] as int),
                ),
            ],
          ],
        ),
      ),
    );
    if (picked != null) setState(() => _categoryId = picked);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.semanticColors;
    final preview = _preview;

    return Padding(
      padding: EdgeInsets.fromLTRB(
          16, 12, 16, 16 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(Icons.bolt, color: colors.expense),
                const SizedBox(width: 8),
                Text('Carga rápida',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _textCtrl,
              autofocus: true,
              maxLength: 200,
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(
                hintText: '15000 super débito',
                counterText: '',
              ),
              onChanged: (_) {
                if (_preview != null || _error != null) {
                  setState(() {
                    _preview = null;
                    _error = null;
                  });
                }
              },
              onSubmitted: (_) => _parse(),
            ),
            if (preview == null) ...[
              const SizedBox(height: 8),
              Text(
                'Escribilo como te salga, en cualquier orden: el monto, qué compraste y, '
                'si querés, cómo pagaste o cuándo. La categoría te la sugerimos. '
                'Ej.: 8500 nafta efectivo, ayer farmacia 12000, netflix 20 usd.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: TextStyle(color: colors.danger)),
            ],
            const SizedBox(height: 12),
            if (preview == null)
              FilledButton(
                onPressed: _parsing ? null : _parse,
                style: FilledButton.styleFrom(backgroundColor: colors.expense),
                child: _parsing
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Cargar'),
              )
            else
              _Preview(
                preview: preview,
                categoryId: _categoryId,
                suggested: _suggestedId != null,
                saving: _saving,
                onPickCategory: _pickCategory,
                onSave: _save,
                onFullForm: _openFullForm,
                onCancel: () => Navigator.of(context).pop(),
              ),
          ],
        ),
      ),
    );
  }
}

class _Preview extends ConsumerWidget {
  const _Preview({
    required this.preview,
    required this.categoryId,
    required this.suggested,
    required this.saving,
    required this.onPickCategory,
    required this.onSave,
    required this.onFullForm,
    required this.onCancel,
  });

  final Map<String, dynamic> preview;
  final int? categoryId;
  final bool suggested;
  final bool saving;
  final ValueChanged<List<dynamic>> onPickCategory;
  final VoidCallback onSave;
  final VoidCallback onFullForm;
  final VoidCallback onCancel;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final colors = context.semanticColors;
    final categories = ref.watch(categoriesProvider).valueOrNull ?? const [];
    final category = categories
        .cast<Map<String, dynamic>>()
        .where((c) => c['id'] == categoryId)
        .firstOrNull;
    final conversion = preview['conversion_display'] as String? ?? '';
    final payment = preview['payment_method_display'] as String? ?? '';
    final description = preview['description'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          preview['amount_display'] as String,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: colors.expense,
                fontWeight: FontWeight.bold,
              ),
        ),
        if (conversion.isNotEmpty)
          Text(conversion, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            Chip(
              avatar: const Icon(Icons.event, size: 16),
              label: Text(preview['date_display'] as String),
            ),
            if (payment.isNotEmpty)
              Chip(
                avatar: const Icon(Icons.payments_outlined, size: 16),
                label: Text(payment),
              ),
          ],
        ),
        if (description.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text('“$description”'),
        ],
        const SizedBox(height: 12),
        InkWell(
          onTap: () => onPickCategory(categories),
          child: InputDecorator(
            decoration: InputDecoration(
              labelText: 'Categoría',
              errorText: category == null ? 'Elegí la categoría' : null,
              suffixIcon: const Icon(Icons.arrow_drop_down),
            ),
            child: Text(category?['name'] as String? ?? 'Elegí la categoría'),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          categoryHint(preview, suggested: suggested),
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: category == null || saving ? null : onSave,
          style: FilledButton.styleFrom(backgroundColor: colors.expense),
          icon: const Icon(Icons.check),
          label: const Text('Guardar'),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: saving ? null : onFullForm,
                child: const Text('Formulario completo'),
              ),
            ),
            const SizedBox(width: 8),
            TextButton(
              onPressed: saving ? null : onCancel,
              child: const Text('Cancelar'),
            ),
          ],
        ),
      ],
    );
  }
}
