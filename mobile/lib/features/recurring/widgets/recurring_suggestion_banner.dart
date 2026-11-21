import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/recurring_provider.dart';

/// Sugerencia de convertir en gasto fijo un gasto que se repite cada mes (DT-053).
/// Muestra una a la vez; si falla la consulta no muestra nada, no es crítica.
class RecurringSuggestionBanner extends ConsumerWidget {
  const RecurringSuggestionBanner({super.key});

  Future<void> _create(
      BuildContext context, WidgetRef ref, Map<String, dynamic> suggestion) async {
    await context.push('/recurring/new', extra: suggestion);
    ref.invalidate(recurringSuggestionsProvider);
  }

  Future<void> _dismiss(
      BuildContext context, WidgetRef ref, Map<String, dynamic> suggestion) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref
          .read(recurringRepositoryProvider)
          .dismissSuggestion(suggestion['key'] as String);
      ref.invalidate(recurringSuggestionsProvider);
      messenger.showSnackBar(
        const SnackBar(content: Text('Listo, no te lo vamos a sugerir de nuevo.')),
      );
    } catch (_) {
      messenger.showSnackBar(
        const SnackBar(content: Text('No se pudo descartar. Probá de nuevo.')),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final suggestions = ref.watch(recurringSuggestionsProvider).valueOrNull;
    if (suggestions == null || suggestions.isEmpty) return const SizedBox.shrink();
    final suggestion = suggestions.first as Map<String, dynamic>;
    final scheme = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      color: scheme.secondaryContainer,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 8, 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.event_repeat, color: scheme.onSecondaryContainer),
                const SizedBox(width: 12),
                Expanded(
                  child: Text.rich(
                    TextSpan(
                      style: TextStyle(color: scheme.onSecondaryContainer),
                      children: [
                        TextSpan(
                          text: suggestion['name'] as String,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        TextSpan(
                          text: ' se repite todos los meses: lo cargaste en los '
                              'últimos ${suggestion['months']} meses por montos '
                              'parecidos. ¿Lo convertís en gasto fijo para que te '
                              'recordemos el vencimiento?',
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => _dismiss(context, ref, suggestion),
                  child: const Text('No, gracias'),
                ),
                FilledButton(
                  onPressed: () => _create(context, ref, suggestion),
                  child: const Text('Crear gasto fijo'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
