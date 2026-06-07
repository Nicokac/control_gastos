import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/dashboard_repository.dart';
import 'package:control_gastos_app/features/dashboard/providers/dashboard_provider.dart';

import 'dashboard_provider_test.mocks.dart';

@GenerateMocks([DashboardRepository])
void main() {
  late MockDashboardRepository mockRepo;
  late ProviderContainer container;

  final fakeData = {
    'total_income': '100000.00',
    'total_expenses': '50000.00',
    'balance': '50000.00',
    'month': 6,
    'year': 2026,
    'pending_recurring': [],
    'total_recurring': 5,
    'expenses_by_category': [],
    'recent_transactions': {'expenses': [], 'income': []},
  };

  setUp(() {
    mockRepo = MockDashboardRepository();
    container = ProviderContainer(
      overrides: [
        dashboardRepositoryProvider.overrideWithValue(mockRepo),
      ],
    );
  });

  tearDown(() => container.dispose());

  group('DashboardNotifier — build', () {
    test('carga los datos del dashboard', () async {
      when(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeData);

      final result = await container.read(dashboardProvider.future);
      expect(result['balance'], equals('50000.00'));
      expect(result['total_recurring'], equals(5));
    });
  });

  group('DashboardNotifier — setMonth', () {
    test('cambiar mes actualiza el estado con nuevos datos', () async {
      final dataMayo = {...fakeData, 'month': 5, 'balance': '10000.00'};
      when(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => dataMayo);

      await container.read(dashboardProvider.future);
      final notifier = container.read(dashboardProvider.notifier);
      await notifier.setMonth(5, 2026);

      expect(notifier.currentMonth, equals(5));
      expect(notifier.currentYear, equals(2026));
      final state = container.read(dashboardProvider).valueOrNull;
      expect(state?['balance'], equals('10000.00'));
    });

    test('no puede avanzar más allá del mes actual', () async {
      when(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeData);

      await container.read(dashboardProvider.future);
      final notifier = container.read(dashboardProvider.notifier);
      final now = DateTime.now();

      await notifier.setMonth(now.month, now.year);
      expect(notifier.currentMonth, equals(now.month));
    });
  });

  group('DashboardNotifier — reload', () {
    test('reload vuelve a llamar al repositorio', () async {
      when(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeData);

      await container.read(dashboardProvider.future);
      final notifier = container.read(dashboardProvider.notifier);
      await notifier.reload();

      verify(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .called(greaterThanOrEqualTo(2));
    });

    test('lastUpdated se actualiza después del reload', () async {
      when(mockRepo.getDashboard(month: anyNamed('month'), year: anyNamed('year')))
          .thenAnswer((_) async => fakeData);

      await container.read(dashboardProvider.future);
      final notifier = container.read(dashboardProvider.notifier);
      final before = notifier.lastUpdated;
      await Future.delayed(const Duration(milliseconds: 10));
      await notifier.reload();

      expect(notifier.lastUpdated, isNotNull);
      expect(notifier.lastUpdated!.isAfter(before!), isTrue);
    });
  });
}
