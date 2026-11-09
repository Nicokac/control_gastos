import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/notification_repository.dart';
import 'package:control_gastos_app/features/auth/providers/auth_provider.dart';
import 'package:control_gastos_app/features/notifications/providers/notifications_provider.dart';
import 'package:control_gastos_app/features/notifications/screens/notifications_screen.dart';

import 'notifications_provider_test.mocks.dart';

class _FakeAuth extends AuthNotifier {
  _FakeAuth(this.user);
  final Map<String, dynamic>? user;

  @override
  Future<Map<String, dynamic>?> build() async => user;
}

Map<String, dynamic> _notification({int id = 1, String? readAt}) => {
      'id': id,
      'type': 'recurring_reminder',
      'title': 'Gastos fijos por vencer',
      'body': 'En 3 días vence Alquiler.',
      'created_at': '2026-11-07T12:00:00Z',
      'read_at': readAt,
    };

@GenerateMocks([NotificationRepository])
void main() {
  late MockNotificationRepository repo;

  ProviderContainer containerFor(Map<String, dynamic>? user) {
    final container = ProviderContainer(
      overrides: [
        notificationRepositoryProvider.overrideWithValue(repo),
        authProvider.overrideWith(() => _FakeAuth(user)),
      ],
    );
    addTearDown(container.dispose);
    return container;
  }

  setUp(() {
    repo = MockNotificationRepository();
    when(repo.getUnreadCount()).thenAnswer((_) async => 2);
    when(repo.markAllRead()).thenAnswer((_) async {});
  });

  group('unreadNotificationsProvider', () {
    test('sin sesión es 0 y no consulta al backend', () async {
      final container = containerFor(null);
      await container.read(authProvider.future);

      expect(await container.read(unreadNotificationsProvider.future), 0);
      verifyNever(repo.getUnreadCount());
    });

    test('con sesión trae la cantidad de no leídas', () async {
      final container = containerFor({'id': 7});
      await container.read(authProvider.future);

      expect(await container.read(unreadNotificationsProvider.future), 2);
    });
  });

  group('NotificationListNotifier', () {
    test('trae el historial y marca como leídos los nuevos', () async {
      when(repo.getNotifications()).thenAnswer((_) async => [_notification()]);
      final container = containerFor({'id': 7});
      final sub = container.listen(notificationListProvider, (_, _) {});

      final items = await container.read(notificationListProvider.future);

      expect(items, hasLength(1));
      expect(items.first['read_at'], isNull, reason: 'en esta visita sigue mostrando el punto');
      verify(repo.markAllRead()).called(1);
      sub.close();
    });

    test('al marcar como leídos recalcula el punto de la campanita', () async {
      when(repo.getNotifications()).thenAnswer((_) async => [_notification()]);
      final container = containerFor({'id': 7});
      await container.read(authProvider.future);
      await container.read(unreadNotificationsProvider.future);
      final sub = container.listen(notificationListProvider, (_, _) {});

      await container.read(notificationListProvider.future);
      when(repo.getUnreadCount()).thenAnswer((_) async => 0);

      expect(await container.read(unreadNotificationsProvider.future), 0);
      sub.close();
    });

    test('si ya estaban todos leídos no vuelve a marcarlos', () async {
      when(repo.getNotifications())
          .thenAnswer((_) async => [_notification(readAt: '2026-11-07T13:00:00Z')]);
      final container = containerFor({'id': 7});
      final sub = container.listen(notificationListProvider, (_, _) {});

      await container.read(notificationListProvider.future);

      verifyNever(repo.markAllRead());
      sub.close();
    });

    test('si falla el marcado igual muestra el historial', () async {
      when(repo.getNotifications()).thenAnswer((_) async => [_notification()]);
      when(repo.markAllRead()).thenThrow(Exception('sin red'));
      final container = containerFor({'id': 7});
      final sub = container.listen(notificationListProvider, (_, _) {});

      final items = await container.read(notificationListProvider.future);

      expect(items, hasLength(1));
      sub.close();
    });
  });

  group('formatNotificationDate', () {
    final now = DateTime(2026, 11, 9, 18, 30);

    test('hoy muestra la hora', () {
      expect(formatNotificationDate(DateTime(2026, 11, 9, 9, 5), now), 'Hoy 09:05');
    });

    test('ayer muestra la hora', () {
      expect(formatNotificationDate(DateTime(2026, 11, 8, 23, 59), now), 'Ayer 23:59');
    });

    test('antes de ayer muestra la fecha', () {
      expect(formatNotificationDate(DateTime(2026, 11, 7, 9), now), '07/11/2026');
    });
  });

  group('iconForNotificationType', () {
    test('cada tipo de aviso tiene su ícono', () {
      expect(iconForNotificationType('recurring_reminder'), Icons.event_repeat);
      expect(iconForNotificationType('recurring_overdue'), Icons.event_busy);
      expect(iconForNotificationType('spending_threshold'), Icons.trending_up);
      expect(iconForNotificationType('category_threshold'), Icons.trending_up);
    });

    test('un tipo desconocido usa el ícono de recordatorio', () {
      expect(iconForNotificationType('otro'), Icons.event_repeat);
      expect(iconForNotificationType(null), Icons.event_repeat);
    });
  });
}
