import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/data/repositories/expense_repository.dart';
import 'package:control_gastos_app/features/categories/screens/categories_screen.dart';
import 'package:control_gastos_app/features/expenses/providers/expense_provider.dart';

const _categories = [
  {
    'id': 1,
    'name': 'Transporte',
    'type': 'EXPENSE',
    'parent': null,
    'is_system': true,
    'color': '#0d6efd',
    'icon': 'bi-bus-front',
  },
  {
    'id': 2,
    'name': 'Combustible',
    'type': 'EXPENSE',
    'parent': 1,
    'is_system': true,
    'color': '#0d6efd',
    'icon': 'bi-fuel-pump',
    'monthly_alert_threshold': null,
  },
  {
    'id': 3,
    'name': 'Peajes',
    'type': 'EXPENSE',
    'parent': 1,
    'is_system': true,
    'color': '#0d6efd',
    'icon': 'bi-sign-turn-right',
    'monthly_alert_threshold': '8000.00',
  },
  {
    'id': 10,
    'name': 'Mascotas',
    'type': 'EXPENSE',
    'parent': null,
    'is_system': false,
    'color': '#20c997',
    'icon': 'bi-tag',
  },
  {
    'id': 11,
    'name': 'Veterinaria',
    'type': 'EXPENSE',
    'parent': 10,
    'is_system': false,
    'color': '#dc3545',
    'icon': 'bi-heart',
    'monthly_alert_threshold': '15000.00',
  },
];

class _FakeExpenseRepository extends ExpenseRepository {
  int fetches = 0;
  final updated = <(int, Map<String, dynamic>)>[];
  final created = <Map<String, dynamic>>[];
  final limits = <(int, double?)>[];

  @override
  Future<void> setCategoryLimit(int id, double? amount) async {
    limits.add((id, amount));
  }

  @override
  Future<List<dynamic>> getCategories() async {
    fetches++;
    return <dynamic>[for (final c in _categories) Map<String, dynamic>.from(c)];
  }

  @override
  Future<Map<String, dynamic>> updateCategory(int id, Map<String, dynamic> data) async {
    updated.add((id, data));
    return {'id': id, ...data};
  }

  @override
  Future<Map<String, dynamic>> createCategory(Map<String, dynamic> data) async {
    created.add(data);
    return {'id': 99, ...data};
  }
}

void main() {
  Future<_FakeExpenseRepository> openScreen(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 2.5;
    addTearDown(tester.view.reset);
    final repo = _FakeExpenseRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [expenseRepositoryProvider.overrideWithValue(repo)],
        child: MaterialApp(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          home: const CategoriesScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return repo;
  }

  Future<void> expand(WidgetTester tester, String group) async {
    await tester.tap(find.text(group));
    await tester.pumpAndSettle();
  }

  Future<void> openSubcatEdit(WidgetTester tester) async {
    await expand(tester, 'Mascotas');
    await tester.tap(find.byTooltip('Editar subcategoría'));
    await tester.pumpAndSettle();
  }

  testWidgets('editar una subcategoría propia abre el formulario precargado', (tester) async {
    await openScreen(tester);
    await openSubcatEdit(tester);

    expect(find.text('Editar subcategoría'), findsWidgets);
    expect(find.widgetWithText(TextField, 'Veterinaria'), findsOneWidget);
    expect(find.widgetWithText(TextField, '15000'), findsOneWidget);
    expect(find.text('Guardar'), findsOneWidget);
  });

  testWidgets('al guardar manda el nuevo límite y recarga la lista', (tester) async {
    final repo = await openScreen(tester);
    await openSubcatEdit(tester);

    await tester.enterText(find.widgetWithText(TextField, '15000'), '20.000');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(repo.updated, hasLength(1));
    final (id, data) = repo.updated.single;
    expect(id, 11);
    expect(data['monthly_alert_threshold'], 20000.0);
    expect(data['name'], 'Veterinaria');
    expect(data['type'], 'EXPENSE');
    expect(data['parent'], 10);
    expect(repo.fetches, 2);
    expect(find.text('Guardar'), findsNothing);
  });

  testWidgets('vaciar el límite lo borra', (tester) async {
    final repo = await openScreen(tester);
    await openSubcatEdit(tester);

    await tester.enterText(find.widgetWithText(TextField, '15000'), '');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    final (_, data) = repo.updated.single;
    expect(data.containsKey('monthly_alert_threshold'), isTrue);
    expect(data['monthly_alert_threshold'], isNull);
  });

  testWidgets('las categorías del sistema no se pueden editar', (tester) async {
    await openScreen(tester);
    await expand(tester, 'Transporte');

    expect(find.text('Combustible'), findsOneWidget);
    expect(find.byTooltip('Editar subcategoría'), findsNothing);
    expect(find.byTooltip('Ocultar para mí'), findsNWidgets(3));
    expect(find.byTooltip('Editar grupo'), findsOneWidget);
  });

  testWidgets('editar un grupo no manda límite', (tester) async {
    final repo = await openScreen(tester);

    await tester.tap(find.byTooltip('Editar grupo'));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextField, 'Mascotas'), findsOneWidget);
    expect(find.textContaining('Umbral de alerta'), findsNothing);

    await tester.enterText(find.widgetWithText(TextField, 'Mascotas'), 'Animales');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    final (id, data) = repo.updated.single;
    expect(id, 10);
    expect(data['name'], 'Animales');
    expect(data.containsKey('monthly_alert_threshold'), isFalse);
    expect(data.containsKey('parent'), isFalse);
  });

  testWidgets('crear una subcategoría sin límite no lo manda', (tester) async {
    final repo = await openScreen(tester);
    await expand(tester, 'Mascotas');

    await tester.tap(find.byTooltip('Agregar subcategoría').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first, 'Peluquería');
    await tester.tap(find.text('Crear'));
    await tester.pumpAndSettle();

    expect(repo.updated, isEmpty);
    expect(repo.created.single['name'], 'Peluquería');
    expect(repo.created.single['parent'], 10);
    expect(repo.created.single.containsKey('monthly_alert_threshold'), isFalse);
  });

  testWidgets('las subcategorías de gasto del sistema tienen botón de límite', (tester) async {
    await openScreen(tester);
    await expand(tester, 'Transporte');

    expect(find.byTooltip('Límite mensual'), findsNWidgets(2));
  });

  testWidgets('definir el límite de una subcategoría del sistema', (tester) async {
    final repo = await openScreen(tester);
    await expand(tester, 'Transporte');

    await tester.tap(find.byTooltip('Límite mensual').first);
    await tester.pumpAndSettle();
    expect(find.text('Límite mensual de Combustible'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '25.000');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(repo.limits, [(2, 25000.0)]);
    expect(repo.fetches, 2);
    expect(repo.updated, isEmpty);
  });

  testWidgets('el límite viene precargado y vaciarlo lo quita', (tester) async {
    final repo = await openScreen(tester);
    await expand(tester, 'Transporte');

    await tester.tap(find.byTooltip('Límite mensual').last);
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextField, '8000'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '');
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(repo.limits, [(3, null)]);
  });

  testWidgets('cancelar no guarda nada', (tester) async {
    final repo = await openScreen(tester);
    await expand(tester, 'Transporte');

    await tester.tap(find.byTooltip('Límite mensual').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();

    expect(repo.limits, isEmpty);
  });
}
