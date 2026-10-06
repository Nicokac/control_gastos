import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/feedback_provider.dart';
import '../../../core/theme/app_semantic_colors.dart';
import '../../../data/services/api_service.dart';

class FeedbackScreen extends ConsumerStatefulWidget {
  const FeedbackScreen({super.key});

  @override
  ConsumerState<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends ConsumerState<FeedbackScreen> {
  static const _tipoChoices = [
    ('bug', 'Bug / Falla', Icons.bug_report_outlined),
    ('mejora', 'Sugerencia de mejora', Icons.lightbulb_outline),
    ('pregunta', 'Pregunta', Icons.help_outline),
    ('otro', 'Otro', Icons.chat_bubble_outline),
  ];

  final _formKey = GlobalKey<FormState>();
  final _mensajeController = TextEditingController();
  String _tipo = 'bug';
  bool _includeTechnicalContext = true;

  @override
  void dispose() {
    _mensajeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final technicalContext = _includeTechnicalContext
        ? ApiService.lastError.value
        : null;

    final error = await ref.read(feedbackProvider.notifier).send(
          tipo: _tipo,
          mensaje: _mensajeController.text.trim(),
          technicalContext: technicalContext,
        );

    if (!mounted) return;

    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          backgroundColor: context.semanticColors.danger,
        ),
      );
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Gracias, tu reporte fue enviado correctamente.'),
        backgroundColor: context.semanticColors.success,
      ),
    );
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(feedbackProvider).isLoading;
    final lastError = ApiService.lastError.value;

    return Scaffold(
      appBar: AppBar(title: const Text('Reportar un problema')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '¿Qué tipo de reporte querés enviar?',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _tipoChoices.map((choice) {
                    final (value, label, icon) = choice;
                    final selected = _tipo == value;
                    return ChoiceChip(
                      selected: selected,
                      label: Text(label),
                      avatar: Icon(icon, size: 18),
                      onSelected: (_) => setState(() => _tipo = value),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 24),
                TextFormField(
                  controller: _mensajeController,
                  maxLines: 6,
                  maxLength: 2000,
                  decoration: const InputDecoration(
                    labelText: 'Mensaje',
                    hintText:
                        'Describí el problema o sugerencia con el mayor detalle posible...',
                    border: OutlineInputBorder(),
                    alignLabelWithHint: true,
                  ),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Escribí un mensaje'
                      : null,
                ),
                if (lastError != null) ...[
                  const SizedBox(height: 16),
                  CheckboxListTile(
                    value: _includeTechnicalContext,
                    onChanged: (v) =>
                        setState(() => _includeTechnicalContext = v ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                    title: const Text(
                      'Incluir el último error técnico detectado',
                      style: TextStyle(fontSize: 14),
                    ),
                    subtitle: Text(
                      lastError,
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: isLoading ? null : _submit,
                    child: isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Enviar reporte'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
