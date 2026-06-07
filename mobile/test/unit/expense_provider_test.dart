import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/expense_repository.dart';
import 'package:control_gastos_app/data/repositories/dashboard_repository.dart';
import 'package:control_gastos_app/features/expenses/providers/expense_provider.dart';
import 'package:control_gastos_app/features/dashboard/providers/dashboard_provider.dart';

import 'expense_provider_test.mocks.dart';

@GenerateMocks([ExpenseRepository, DashboardRepository])
void main() {
  late MockExpenseRepository mockRepo;
  late MockDashboardRepository mockDashboardRepo;
  late ProviderContainer container;

  final fakeExpenses = [
    {'id': 1, 'description': 'Supermercado', 'amount_ars': '5000.00', 'date': '2026-06-01'},
    {'id': 2, 'description': 'Combustible', 'amount_ars': '3000.00', 'date': '2026-06-02'},
  ];

  setUp(() {
    mockRepo = MockExpenseRepository();
    mockDashboardRepo = MockDashboardRepository();
    when(mockDashboardRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => {});
    container = ProviderContainer(
      overrides: [
        expenseRepositoryProvider.overrideWithValue(mockRepo),
        dashboardRepositoryProvider.overrideWithValue(mockDashboardRepo),
      ],
    );
  });

  tearDown(() => container.dispose());

  group('ExpenseListNotifier — build', () {
    test('carga la lista de gastos', () async {
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);

      final result = await container.read(expenseListProvider.future);
      expect(result, hasLength(2));
      expect(result[0]['description'], equals('Supermercado'));
    });
  });

  group('ExpenseListNotifier — setMonth', () {
    test('cambiar mes recarga la lista', () async {
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);

      await container.read(expenseListProvider.future);
      final notifier = container.read(expenseListProvider.notifier);
      await notifier.setMonth(5, 2026);

      expect(notifier.currentMonth, equals(5));
      expect(notifier.currentYear, equals(2026));
      verify(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .called(greaterThanOrEqualTo(2));
    });
  });

  group('ExpenseListNotifier — create', () {
    test('create exitoso retorna true y recarga', () async {
      final newExpense = {'description': 'Nuevo', 'amount_ars': '1000.00'};
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);
      when(mockRepo.createExpense(any)).thenAnswer((_) async => newExpense);

      await container.read(expenseListProvider.future);
      final notifier = container.read(expenseListProvider.notifier);
      final result = await notifier.create(newExpense);

      expect(result, isTrue);
      verify(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .called(greaterThanOrEqualTo(2));
    });

    test('create fallido retorna false', () async {
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);
      when(mockRepo.createExpense(any)).thenThrow(Exception('Error de red'));

      await container.read(expenseListProvider.future);
      final notifier = container.read(expenseListProvider.notifier);
      final result = await notifier.create({});

      expect(result, isFalse);
    });
  });

  group('ExpenseListNotifier — delete', () {
    test('delete exitoso retorna true', () async {
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);
      when(mockRepo.deleteExpense(1)).thenAnswer((_) async => {});

      await container.read(expenseListProvider.future);
      final notifier = container.read(expenseListProvider.notifier);
      final result = await notifier.delete(1);

      expect(result, isTrue);
    });

    test('delete fallido retorna false', () async {
      when(mockRepo.getExpenses(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeExpenses);
      when(mockRepo.deleteExpense(99)).thenThrow(Exception('Not found'));

      await container.read(expenseListProvider.future);
      final notifier = container.read(expenseListProvider.notifier);
      final result = await notifier.delete(99);

      expect(result, isFalse);
    });
  });
}
