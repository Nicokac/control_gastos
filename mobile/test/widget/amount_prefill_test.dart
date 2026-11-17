import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/features/dashboard/providers/dashboard_provider.dart';
import 'package:control_gastos_app/features/expenses/providers/expense_provider.dart';
import 'package:control_gastos_app/features/expenses/screens/expense_form_screen.dart';
import 'package:control_gastos_app/features/income/providers/income_provider.dart';
import 'package:control_gastos_app/features/income/screens/income_form_screen.dart';
import 'package:control_gastos_app/features/savings/screens/saving_form_screen.dart';
import 'package:control_gastos_app/features/shared_expenses/providers/shared_expense_provider.dart';
import 'package:control_gastos_app/features/shared_expenses/screens/shared_expense_form_screen.dart';

import '../unit/expense_provider_test.mocks.dart';

// Al editar, la API devuelve el monto como "8500.00"; el formulario lo lee en
// formato argentino (el punto es de miles), así que precargado tal cual se
// guardaba como 850000.

// Mismos tipos que el JSON de la API (Map<String, dynamic>): el formulario hace
// firstWhere(orElse: () => {}) y con mapas const de otro tipo falla el test.
final _expenseCategories = <dynamic>[
  <String, dynamic>{'id': 1, 'name': 'Comida', 'type': 'EXPENSE', 'parent': null},
  <String, dynamic>{'id': 2, 'name': 'Supermercado', 'type': 'EXPENSE', 'parent': 1},
];

void main() {
  Future<void> pumpForm(WidgetTester tester, Widget form, {List<Override> overrides = const []}) async {
    // 480 dp: la fuente de los tests (Ahem) es más ancha que la real.
    tester.view.physicalSize = const Size(1440, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    // El formulario cierra con context.pop() al guardar: necesita un GoRouter con algo debajo.
    final router = GoRouter(
      initialLocation: '/form',
      routes: [
        GoRoute(
          path: '/',
          builder: (_, _) => const Scaffold(body: Text('lista')),
          routes: [GoRoute(path: 'form', builder: (_, _) => form)],
        ),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: overrides,
        child: MaterialApp.router(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          routerConfig: router,
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('el formulario de gasto precarga 8500.00 como 8500', (tester) async {
    await pumpForm(
      tester,
      const ExpenseFormScreen(existing: {
        'id': 1,
        'amount': '8500.00',
        'date': '2026-11-16',
        'category': 2,
        'currency': 'ARS',
      }),
      overrides: [categoriesProvider.overrideWith((ref) async => _expenseCategories)],
    );

    expect(find.text('8500'), findsOneWidget);
  });

  testWidgets('editar un gasto sin tocar el monto lo guarda igual', (tester) async {
    final repo = MockExpenseRepository();
    final dashboardRepo = MockDashboardRepository();
    when(repo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => []);
    when(repo.updateExpense(any, any)).thenAnswer((_) async => {});
    when(dashboardRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => {});
    await pumpForm(
      tester,
      const ExpenseFormScreen(existing: {
        'id': 7,
        'amount': '1500.50',
        'date': '2026-11-16',
        'description': 'Almuerzo',
        'category': 2,
        'currency': 'ARS',
      }),
      overrides: [
        expenseRepositoryProvider.overrideWithValue(repo),
        dashboardRepositoryProvider.overrideWithValue(dashboardRepo),
        categoriesProvider.overrideWith((ref) async => _expenseCategories),
      ],
    );

    await tester.tap(find.byType(FilledButton).last);
    await tester.pumpAndSettle();

    final sent = verify(repo.updateExpense(7, captureAny)).captured.single as Map<String, dynamic>;
    expect(sent['amount'], 1500.5);
  });

  testWidgets('el formulario de ingreso precarga 8500.00 como 8500', (tester) async {
    await pumpForm(
      tester,
      const IncomeFormScreen(existing: {
        'id': 1,
        'amount': '8500.00',
        'date': '2026-11-16',
        'category': 5,
        'currency': 'ARS',
      }),
      overrides: [incomeCategoriesProvider.overrideWith((ref) async => [])],
    );

    expect(find.text('8500'), findsOneWidget);
  });

  testWidgets('el formulario de gasto compartido precarga 8500.00 como 8500', (tester) async {
    await pumpForm(
      tester,
      const SharedExpenseFormScreen(existing: {
        'id': 1,
        'amount': '8500.00',
        'date': '2026-11-16',
        'category': 2,
      }),
      overrides: [
        sharedCategoriesProvider.overrideWith((ref) async => []),
        householdMembersProvider.overrideWith((ref) async => []),
      ],
    );

    expect(find.text('8500'), findsOneWidget);
  });

  testWidgets('el formulario de meta de ahorro precarga 150000.00 como 150000', (tester) async {
    await pumpForm(
      tester,
      const SavingFormScreen(existing: {
        'id': 1,
        'name': 'Vacaciones',
        'target_amount': '150000.00',
      }),
    );

    expect(find.text('150000'), findsOneWidget);
  });
}
