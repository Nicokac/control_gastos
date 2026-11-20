import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/data/repositories/category_rule_repository.dart';
import 'package:control_gastos_app/features/categories/providers/category_rule_provider.dart';
import 'package:control_gastos_app/features/categories/screens/category_rules_screen.dart';
import 'package:control_gastos_app/features/expenses/providers/expense_provider.dart';

const _categories = [
  {'id': 1, 'name': 'Comida', 'type': 'EXPENSE', 'parent': null},
  {'id': 2, 'name': 'Supermercado', 'type': 'EXPENSE', 'parent': 1, 'parent_name': 'Comida'},
  {'id': 3, 'name': 'Verdulería', 'type': 'EXPENSE', 'parent': 1, 'parent_name': 'Comida'},
];

const _superRule = {
  'id': 7,
  'pattern': 'super',
  'category': 2,
  'category_name': 'Supermercado',
  'group_name': 'Comida',
};

class _FakeRuleRepository implements CategoryRuleRepository {
  _FakeRuleRepository(this.rules);

  List<dynamic> rules;
  int fetches = 0;
  final saved = <Map<String, dynamic>>[];
  final deleted = <int>[];
  CategoryRuleException? saveError;

  @override
  Future<List<dynamic>> getRules() async {
    fetches++;
    return rules;
  }

  @override
  Future<void> saveRule({int? id, required String pattern, required int category}) async {
    if (saveError != null) throw saveError!;
    saved.add({'id': id, 'pattern': pattern, 'category': category});
  }

  @override
  Future<void> deleteRule(int id) async => deleted.add(id);
}

void main() {
  Future<_FakeRuleRepository> openScreen(WidgetTester tester, List<dynamic> rules) async {
    final repo = _FakeRuleRepository(rules);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          categoryRuleRepositoryProvider.overrideWithValue(repo),
          categoriesProvider.overrideWith((ref) async => _categories),
        ],
        child: MaterialApp(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          home: const CategoryRulesScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return repo;
  }

  testWidgets('lista cada regla con su grupo y subcategoría', (tester) async {
    await openScreen(tester, [_superRule]);

    expect(find.text('“super”'), findsOneWidget);
    expect(find.text('Comida › Supermercado'), findsOneWidget);
  });

  testWidgets('sin reglas explica cómo se crean', (tester) async {
    await openScreen(tester, []);

    expect(find.textContaining('Todavía no tenés reglas'), findsOneWidget);
  });

  testWidgets('crear una regla manda el texto y la categoría y recarga la lista',
      (tester) async {
    final repo = await openScreen(tester, []);

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'farmacia');
    await tester.tap(find.text('Elegí la categoría'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Verdulería'));
    await tester.pumpAndSettle();
    expect(find.text('Comida › Verdulería'), findsOneWidget);
    await tester.tap(find.text('Crear regla'));
    await tester.pumpAndSettle();

    expect(repo.saved, [
      {'id': null, 'pattern': 'farmacia', 'category': 3},
    ]);
    expect(find.text('Nueva regla'), findsNothing);
    expect(repo.fetches, 2);
  });

  testWidgets('sin texto ni categoría no llama al backend', (tester) async {
    final repo = await openScreen(tester, []);

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Crear regla'));
    await tester.pumpAndSettle();

    expect(find.text('Escribí al menos una palabra.'), findsOneWidget);
    expect(find.text('Elegí la categoría.'), findsOneWidget);
    expect(repo.saved, isEmpty);
  });

  testWidgets('el error del backend aparece debajo del campo y la hoja sigue abierta',
      (tester) async {
    final repo = await openScreen(tester, [_superRule]);
    repo.saveError =
        const CategoryRuleException({'pattern': 'Ya tenés una regla con ese texto.'});

    await tester.tap(find.byType(FloatingActionButton));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Súper');
    await tester.tap(find.text('Elegí la categoría'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supermercado'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Crear regla'));
    await tester.pumpAndSettle();

    expect(find.text('Ya tenés una regla con ese texto.'), findsOneWidget);
    expect(find.text('Nueva regla'), findsOneWidget);
  });

  testWidgets('tocar una regla la abre para editar con sus datos', (tester) async {
    final repo = await openScreen(tester, [_superRule]);

    await tester.tap(find.text('“super”'));
    await tester.pumpAndSettle();
    expect(find.text('Editar regla'), findsOneWidget);
    expect(find.widgetWithText(TextField, 'super'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'supermercado');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(repo.saved, [
      {'id': 7, 'pattern': 'supermercado', 'category': 2},
    ]);
  });

  testWidgets('eliminar pide confirmación', (tester) async {
    final repo = await openScreen(tester, [_superRule]);

    await tester.tap(find.byTooltip('Eliminar regla super'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
    expect(repo.deleted, isEmpty);

    await tester.tap(find.byTooltip('Eliminar regla super'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Eliminar'));
    await tester.pumpAndSettle();
    expect(repo.deleted, [7]);
  });
}
