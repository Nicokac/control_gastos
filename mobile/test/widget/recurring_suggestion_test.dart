import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/data/repositories/recurring_repository.dart';
import 'package:control_gastos_app/features/recurring/providers/recurring_provider.dart';
import 'package:control_gastos_app/features/recurring/screens/recurring_form_screen.dart';
import 'package:control_gastos_app/features/recurring/widgets/recurring_suggestion_banner.dart';

const _netflix = {
  'key': 'netflix',
  'name': 'Netflix',
  'category': 2,
  'category_name': 'Streaming',
  'group_name': 'Entretenimiento',
  'due_day': 7,
  'amount': '9499.00',
  'months': 3,
  'expense_count': 3,
};

const _categories = [
  {'id': 1, 'name': 'Entretenimiento', 'type': 'EXPENSE', 'parent': null},
  {'id': 2, 'name': 'Streaming', 'type': 'EXPENSE', 'parent': 1},
];

class _FakeRecurringRepository extends RecurringRepository {
  _FakeRecurringRepository(this.suggestions);

  List<dynamic> suggestions;
  int suggestionFetches = 0;
  final dismissed = <String>[];
  final created = <Map<String, dynamic>>[];
  bool failDismiss = false;

  @override
  Future<List<dynamic>> getSuggestions() async {
    suggestionFetches++;
    return suggestions;
  }

  @override
  Future<void> dismissSuggestion(String key) async {
    if (failDismiss) throw Exception('sin red');
    dismissed.add(key);
    suggestions = [];
  }

  @override
  Future<Map<String, dynamic>> createRecurring(Map<String, dynamic> data) async {
    created.add(data);
    return {'id': 1, ...data};
  }

  @override
  Future<List<dynamic>> getRecurring() async => [];

  @override
  // Como el JSON real: List<dynamic> de Map<String, dynamic>, no la lista const tipada.
  Future<List<dynamic>> getCategories() async =>
      <dynamic>[for (final c in _categories) Map<String, dynamic>.from(c)];
}

void main() {
  Future<(_FakeRecurringRepository, GoRouter)> pumpApp(
    WidgetTester tester,
    List<dynamic> suggestions,
  ) async {
    final repo = _FakeRecurringRepository(suggestions);
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (_, _) => const Scaffold(body: RecurringSuggestionBanner()),
        ),
        GoRoute(
          path: '/recurring/new',
          builder: (_, s) =>
              RecurringFormScreen(suggestion: s.extra as Map<String, dynamic>?),
        ),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [recurringRepositoryProvider.overrideWithValue(repo)],
        child: MaterialApp.router(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();
    return (repo, router);
  }

  group('RecurringSuggestionBanner', () {
    testWidgets('muestra la primera sugerencia', (tester) async {
      await pumpApp(tester, [_netflix]);

      expect(find.textContaining('se repite todos los meses'), findsOneWidget);
      expect(find.textContaining('últimos 3 meses'), findsOneWidget);
      expect(find.text('Crear gasto fijo'), findsOneWidget);
    });

    testWidgets('sin sugerencias no muestra nada', (tester) async {
      await pumpApp(tester, []);

      expect(find.textContaining('se repite todos los meses'), findsNothing);
    });

    testWidgets('"No, gracias" la descarta y la oculta', (tester) async {
      final (repo, _) = await pumpApp(tester, [_netflix]);

      await tester.tap(find.text('No, gracias'));
      await tester.pumpAndSettle();

      expect(repo.dismissed, ['netflix']);
      expect(find.textContaining('se repite todos los meses'), findsNothing);
      expect(find.text('Listo, no te lo vamos a sugerir de nuevo.'), findsOneWidget);
    });

    testWidgets('si falla el descarte lo avisa y la sugerencia sigue', (tester) async {
      final (repo, _) = await pumpApp(tester, [_netflix]);
      repo.failDismiss = true;

      await tester.tap(find.text('No, gracias'));
      await tester.pumpAndSettle();

      expect(find.text('No se pudo descartar. Probá de nuevo.'), findsOneWidget);
      expect(find.textContaining('se repite todos los meses'), findsOneWidget);
    });
  });

  group('Crear gasto fijo desde la sugerencia', () {
    testWidgets('abre el formulario precargado', (tester) async {
      await pumpApp(tester, [_netflix]);

      await tester.tap(find.text('Crear gasto fijo'));
      await tester.pumpAndSettle();

      expect(find.widgetWithText(TextFormField, 'Netflix'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, '9499,00'), findsOneWidget);
      expect(
        find.textContaining('los 3 pagos detectados quedan vinculados'),
        findsOneWidget,
      );
      await tester.scrollUntilVisible(
        find.text('Streaming'),
        200,
        scrollable: find
            .descendant(of: find.byType(ListView), matching: find.byType(Scrollable))
            .first,
      );
      expect(find.text('Entretenimiento'), findsOneWidget);
      expect(find.text('Streaming'), findsOneWidget);
    });

    testWidgets('al guardar manda la clave de la sugerencia y vuelve a consultar',
        (tester) async {
      final (repo, _) = await pumpApp(tester, [_netflix]);

      await tester.tap(find.text('Crear gasto fijo'));
      await tester.pumpAndSettle();
      repo.suggestions = [];
      await tester.tap(find.text('Guardar'));
      await tester.pumpAndSettle();

      expect(repo.created, hasLength(1));
      expect(repo.created.single['suggestion'], 'netflix');
      expect(repo.created.single['name'], 'Netflix');
      expect(repo.created.single['category'], 2);
      expect(repo.created.single['due_day'], 7);
      expect(repo.created.single['estimated_amount'], 9499.0);
      expect(repo.suggestionFetches, 2);
      expect(find.textContaining('se repite todos los meses'), findsNothing);
    });

    testWidgets('un gasto fijo creado a mano no manda sugerencia', (tester) async {
      final (repo, router) = await pumpApp(tester, []);

      router.push('/recurring/new');
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextFormField).first, 'Luz');
      expect(find.textContaining('pagos detectados'), findsNothing);
      expect(repo.created, isEmpty);
    });
  });
}
