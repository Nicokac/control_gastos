import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/recurring_repository.dart';
import 'package:control_gastos_app/data/repositories/dashboard_repository.dart';
import 'package:control_gastos_app/features/recurring/providers/recurring_provider.dart';
import 'package:control_gastos_app/features/dashboard/providers/dashboard_provider.dart';
import 'recurring_provider_test.mocks.dart';

@GenerateMocks([RecurringRepository, DashboardRepository])
void main() {
  late MockRecurringRepository mockRepo;
  late MockDashboardRepository mockDashboardRepo;
  late ProviderContainer container;

  final fakeList = [
    {'id': 1, 'name': 'Flow', 'status': 'pending', 'last_amount': '5000.00'},
    {'id': 2, 'name': 'Pilates', 'status': 'paid', 'last_amount': '3000.00'},
  ];

  setUp(() {
    mockRepo = MockRecurringRepository();
    mockDashboardRepo = MockDashboardRepository();
    when(mockDashboardRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
        .thenAnswer((_) async => {});
    container = ProviderContainer(
      overrides: [
        recurringRepositoryProvider.overrideWithValue(mockRepo),
        dashboardRepositoryProvider.overrideWithValue(mockDashboardRepo),
      ],
    );
  });

  tearDown(() => container.dispose());

  group('RecurringListNotifier — build', () {
    test('carga la lista de recurrentes', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);

      final result = await container.read(recurringListProvider.future);
      expect(result, hasLength(2));
      expect(result[0]['name'], equals('Flow'));
    });
  });

  group('RecurringListNotifier — markPaid', () {
    test('markPaid exitoso recarga la lista', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);
      when(mockRepo.markPaid(1, amount: anyNamed('amount')))
          .thenAnswer((_) async => {'detail': 'Pago registrado.'});

      await container.read(recurringListProvider.future);
      final notifier = container.read(recurringListProvider.notifier);
      final error = await notifier.markPaid(1);

      expect(error, isNull);
      verify(mockRepo.getRecurring()).called(greaterThanOrEqualTo(2));
    });

    test('markPaid duplicado retorna mensaje de error', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);
      when(mockRepo.markPaid(1, amount: anyNamed('amount')))
          .thenThrow(Exception('ya fue registrado este mes'));

      await container.read(recurringListProvider.future);
      final notifier = container.read(recurringListProvider.notifier);
      final error = await notifier.markPaid(1);

      expect(error, contains('ya fue registrado'));
    });
  });

  group('RecurringListNotifier — unmarkPaid', () {
    test('unmarkPaid exitoso retorna null', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);
      when(mockRepo.unmarkPaid(2)).thenAnswer((_) async => {});

      await container.read(recurringListProvider.future);
      final notifier = container.read(recurringListProvider.notifier);
      final error = await notifier.unmarkPaid(2);

      expect(error, isNull);
    });

    test('unmarkPaid sin pago retorna mensaje de error', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);
      when(mockRepo.unmarkPaid(2))
          .thenThrow(Exception('No hay pago registrado este mes'));

      await container.read(recurringListProvider.future);
      final notifier = container.read(recurringListProvider.notifier);
      final error = await notifier.unmarkPaid(2);

      expect(error, contains('No hay pago'));
    });
  });

  group('RecurringListNotifier — delete', () {
    test('delete exitoso retorna true', () async {
      when(mockRepo.getRecurring()).thenAnswer((_) async => fakeList);
      when(mockRepo.deleteRecurring(1)).thenAnswer((_) async => {});

      await container.read(recurringListProvider.future);
      final notifier = container.read(recurringListProvider.notifier);
      final result = await notifier.delete(1);

      expect(result, isTrue);
    });
  });
}
