import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_semantic_colors.dart';
import '../../../core/widgets/error_state_view.dart';
import '../../../core/widgets/list_skeleton.dart';
import '../../../data/repositories/category_rule_repository.dart';
import '../../expenses/providers/expense_provider.dart';
import '../../expenses/widgets/quick_expense_sheet.dart';
import '../providers/category_rule_provider.dart';

/// Reglas de categorización: "si la descripción contiene estas palabras, va a esta categoría".
class CategoryRulesScreen extends ConsumerWidget {
  const CategoryRulesScreen({super.key});

  Future<void> _openForm(BuildContext context, WidgetRef ref,
      [Map<String, dynamic>? rule]) async {
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => _RuleFormSheet(rule: rule),
    );
    if (saved == true) ref.invalidate(categoryRulesProvider);
  }

  Future<void> _confirmDelete(
      BuildContext context, WidgetRef ref, Map<String, dynamic> rule) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar regla'),
        content: Text('¿Eliminar la regla “${rule['pattern']}”?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(
                foregroundColor: context.semanticColors.danger),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(categoryRuleRepositoryProvider).deleteRule(rule['id'] as int);
      ref.invalidate(categoryRulesProvider);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo eliminar la regla')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rulesAsync = ref.watch(categoryRulesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Reglas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Nueva regla',
            onPressed: () => _openForm(context, ref),
          ),
        ],
      ),
      body: rulesAsync.when(
        loading: () => const ListSkeleton(itemCount: 4),
        error: (e, _) => ErrorStateView(
          error: e,
          onRetry: () => ref.invalidate(categoryRulesProvider),
        ),
        data: (rules) => RefreshIndicator(
          onRefresh: () => ref.refresh(categoryRulesProvider.future),
          child: ListView(
            padding: const EdgeInsets.only(bottom: 88),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Text(
                  'Si la descripción de un gasto contiene estas palabras, te sugerimos '
                  'la categoría elegida en la carga rápida y al importar resúmenes.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
              if (rules.isEmpty)
                const _EmptyRules()
              else
                for (final rule in rules.cast<Map<String, dynamic>>()) ...[
                  ListTile(
                    title: Text('“${rule['pattern']}”'),
                    subtitle: Text(
                        '${rule['group_name'] ?? ''} › ${rule['category_name']}'),
                    onTap: () => _openForm(context, ref, rule),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      tooltip: 'Eliminar regla ${rule['pattern']}',
                      onPressed: () => _confirmDelete(context, ref, rule),
                    ),
                  ),
                  const Divider(height: 1, indent: 16),
                ],
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openForm(context, ref),
        tooltip: 'Nueva regla',
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _EmptyRules extends StatelessWidget {
  const _EmptyRules();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(32, 48, 32, 0),
      child: Column(
        children: [
          Icon(Icons.auto_fix_high, size: 56, color: Theme.of(context).hintColor),
          const SizedBox(height: 12),
          Text(
            'Todavía no tenés reglas. Se crean solas cuando cambiás la categoría '
            'sugerida en la carga rápida o al importar un resumen.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Theme.of(context).hintColor),
          ),
        ],
      ),
    );
  }
}

class _RuleFormSheet extends ConsumerStatefulWidget {
  const _RuleFormSheet({this.rule});

  final Map<String, dynamic>? rule;

  @override
  ConsumerState<_RuleFormSheet> createState() => _RuleFormSheetState();
}

class _RuleFormSheetState extends ConsumerState<_RuleFormSheet> {
  late final _patternCtrl =
      TextEditingController(text: widget.rule?['pattern'] as String? ?? '');
  late int? _categoryId = widget.rule?['category'] as int?;
  Map<String, String> _errors = const {};
  bool _saving = false;

  @override
  void dispose() {
    _patternCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickCategory(List<dynamic> categories) async {
    final picked =
        await pickExpenseCategory(context, categories, selectedId: _categoryId);
    if (picked != null) {
      setState(() {
        _categoryId = picked;
        _errors = {..._errors}..remove('category');
      });
    }
  }

  Future<void> _save() async {
    final pattern = _patternCtrl.text.trim();
    final errors = {
      if (pattern.isEmpty) 'pattern': 'Escribí al menos una palabra.',
      if (_categoryId == null) 'category': 'Elegí la categoría.',
    };
    if (errors.isNotEmpty) {
      setState(() => _errors = errors);
      return;
    }
    setState(() {
      _saving = true;
      _errors = const {};
    });
    try {
      await ref.read(categoryRuleRepositoryProvider).saveRule(
            id: widget.rule?['id'] as int?,
            pattern: pattern,
            category: _categoryId!,
          );
      if (mounted) Navigator.of(context).pop(true);
    } on CategoryRuleException catch (e) {
      if (mounted) setState(() => _errors = e.fieldErrors);
    } catch (_) {
      if (mounted) {
        setState(() => _errors = {'pattern': 'No se pudo guardar. Probá de nuevo.'});
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = ref.watch(categoriesProvider).valueOrNull ?? const [];
    final category = categories
        .cast<Map<String, dynamic>>()
        .where((c) => c['id'] == _categoryId)
        .firstOrNull;
    final isEdit = widget.rule != null;

    return Padding(
      padding: EdgeInsets.fromLTRB(
          16, 16, 16, 16 + MediaQuery.of(context).viewInsets.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(isEdit ? 'Editar regla' : 'Nueva regla',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          TextField(
            controller: _patternCtrl,
            autofocus: !isEdit,
            maxLength: 100,
            textInputAction: TextInputAction.done,
            decoration: InputDecoration(
              labelText: 'Si la descripción contiene',
              hintText: 'Ej.: super, netflix, farmacia',
              helperText: 'Palabras completas, sin importar mayúsculas ni acentos.',
              helperMaxLines: 2,
              errorText: _errors['pattern'],
            ),
            onChanged: (_) {
              if (_errors.containsKey('pattern')) {
                setState(() => _errors = {..._errors}..remove('pattern'));
              }
            },
          ),
          const SizedBox(height: 8),
          InkWell(
            onTap: () => _pickCategory(categories),
            child: InputDecorator(
              decoration: InputDecoration(
                labelText: 'Sugerir la categoría',
                suffixIcon: const Icon(Icons.arrow_drop_down),
                errorText: _errors['category'],
              ),
              child: Text(category == null
                  ? 'Elegí la categoría'
                  : '${category['parent_name'] ?? ''} › ${category['name']}'),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: _saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(isEdit ? 'Guardar' : 'Crear regla'),
          ),
        ],
      ),
    );
  }
}
