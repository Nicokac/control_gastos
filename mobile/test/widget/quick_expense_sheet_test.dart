import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/core/utils/formatters.dart';
import 'package:control_gastos_app/data/repositories/expense_repository.dart';
import 'package:control_gastos_app/features/dashboard/providers/dashboard_provider.dart';
import 'package:control_gastos_app/features/expenses/providers/expense_provider.dart';
import 'package:control_gastos_app/features/expenses/widgets/quick_expense_sheet.dart';

import '../unit/expense_provider_test.mocks.dart';

const _categories = [
  {'id': 1, 'name': 'Comida', 'type': 'EXPENSE', 'parent': null},
  {'id': 2, 'name': 'Supermercado', 'type': 'EXPENSE', 'parent': 1},
  {'id': 3, 'name': 'Verdulería', 'type': 'EXPENSE', 'parent': 1},
  {'id': 4, 'name': 'Oculta', 'type': 'EXPENSE', 'parent': 1, 'is_hidden': true},
  {'id': 5, 'name': 'Sueldo', 'type': 'INCOME', 'parent': null},
];

Map<String, dynamic> _preview({int? categoryId = 2, String source = 'historial'}) => {
      'ok': true,
      'amount': '8500.00',
      'amount_display': r'$ 8.500',
      'conversion_display': '',
      'currency': 'ARS',
      'exchange_rate': '1',
      'date': '2026-11-16',
      'date_display': '16/11/2026',
      'payment_method': 'CASH',
      'payment_method_display': 'Efectivo',
      'description': 'verduleria don pepe',
      'category_id': categoryId,
      'category_name': categoryId == null ? null : 'Supermercado',
      'category_source': categoryId == null ? null : source,
      'category_rule': '',
    };

void main() {
  late MockExpenseRepository repo;
  late MockDashboardRepository dashboardRepo;

  setUp(() {
    repo = MockExpenseRepository();
    dashboardRepo = MockDashboardRepository();
    when(repo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => []);
    when(dashboardRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => {});
  });

  Future<void> openSheet(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          expenseRepositoryProvider.overrideWithValue(repo),
          dashboardRepositoryProvider.overrideWithValue(dashboardRepo),
          categoriesProvider.overrideWith((ref) async => _categories),
        ],
        child: MaterialApp(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          home: Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () => showQuickExpenseSheet(context),
                child: const Text('abrir'),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('abrir'));
    await tester.pumpAndSettle();
  }

  Future<void> typeAndLoad(WidgetTester tester, String text) async {
    await tester.enterText(find.byType(TextField), text);
    await tester.tap(find.text('Cargar'));
    await tester.pumpAndSettle();
  }

  testWidgets('muestra la vista previa con la categoría sugerida y su origen', (tester) async {
    when(repo.quickParse('8500 verduleria don pepe efectivo'))
        .thenAnswer((_) async => _preview());
    await openSheet(tester);

    await typeAndLoad(tester, '8500 verduleria don pepe efectivo');

    expect(find.text(r'$ 8.500'), findsOneWidget);
    expect(find.text('Efectivo'), findsOneWidget);
    expect(find.text('16/11/2026'), findsOneWidget);
    expect(find.text('Supermercado'), findsOneWidget);
    expect(find.textContaining('Sugerida por tus gastos anteriores.'), findsOneWidget);
  });

  testWidgets('si el backend no entiende el texto muestra su mensaje', (tester) async {
    when(repo.quickParse('super'))
        .thenThrow(const QuickEntryException('No encontré el monto.'));
    await openSheet(tester);

    await typeAndLoad(tester, 'super');

    expect(find.text('No encontré el monto.'), findsOneWidget);
    expect(find.text('Guardar'), findsNothing);
  });

  testWidgets('sin categoría sugerida pide elegirla y no deja guardar', (tester) async {
    when(repo.quickParse('8500 cosa')).thenAnswer((_) async => _preview(categoryId: null));
    await openSheet(tester);

    await typeAndLoad(tester, '8500 cosa');

    expect(find.textContaining('No pude adivinar la categoría'), findsOneWidget);
    final save = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Guardar'));
    expect(save.onPressed, isNull);
  });

  testWidgets('una sugerencia oculta se trata como sin sugerencia', (tester) async {
    when(repo.quickParse('8500 cosa')).thenAnswer((_) async => _preview(categoryId: 4));
    await openSheet(tester);

    await typeAndLoad(tester, '8500 cosa');

    expect(find.textContaining('No pude adivinar la categoría'), findsOneWidget);
  });

  testWidgets('al corregir la categoría guarda con la sugerida y avisa la regla aprendida',
      (tester) async {
    when(repo.quickParse('8500 verduleria don pepe efectivo'))
        .thenAnswer((_) async => _preview());
    when(repo.quickCreate(any)).thenAnswer((_) async => {
          'id': 9,
          'category_name': 'Verdulería',
          'learned_rule': {'pattern': 'verduleria don pepe', 'category_name': 'Verdulería'},
        });
    await openSheet(tester);
    await typeAndLoad(tester, '8500 verduleria don pepe efectivo');

    await tester.tap(find.text('Supermercado'));
    await tester.pumpAndSettle();
    expect(find.text('Oculta'), findsNothing);
    await tester.tap(find.text('Verdulería'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    final sent = verify(repo.quickCreate(captureAny)).captured.single as Map<String, dynamic>;
    expect(sent['category'], 3);
    expect(sent['suggested_category'], 2);
    expect(sent['amount'], '8500.00');
    expect(sent['payment_method'], 'CASH');
    expect(find.byType(QuickExpenseSheet), findsNothing);
    expect(find.textContaining('Desde ahora, “verduleria don pepe” se sugiere en Verdulería.'),
        findsOneWidget);
  });

  testWidgets('si no se puede guardar lo avisa y la hoja queda abierta', (tester) async {
    when(repo.quickParse('8500 super')).thenAnswer((_) async => _preview());
    when(repo.quickCreate(any)).thenThrow(Exception('sin red'));
    await openSheet(tester);
    await typeAndLoad(tester, '8500 super');

    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();

    expect(find.text('No pudimos guardar el gasto. Probá de nuevo.'), findsOneWidget);
    expect(find.byType(QuickExpenseSheet), findsOneWidget);
  });

  group('apiAmountToInput', () {
    test('un monto entero queda sin decimales', () {
      expect(apiAmountToInput('8500.00'), '8500');
      expect(parseArgentineAmount(apiAmountToInput('8500.00')), 8500);
    });

    test('los decimales usan coma', () {
      expect(apiAmountToInput('1500.50'), '1500,50');
      expect(parseArgentineAmount(apiAmountToInput('1500.50')), 1500.5);
    });
  });
}
