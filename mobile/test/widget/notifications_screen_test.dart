import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/features/auth/providers/auth_provider.dart';
import 'package:control_gastos_app/features/notifications/providers/notifications_provider.dart';
import 'package:control_gastos_app/features/notifications/screens/notifications_screen.dart';

import '../unit/notifications_provider_test.mocks.dart';

class _FakeAuth extends AuthNotifier {
  _FakeAuth(this.user, {this.saveOk = true});
  final Map<String, dynamic> user;
  final bool saveOk;
  final saved = <Map<String, dynamic>>[];

  @override
  Future<Map<String, dynamic>?> build() async => user;

  @override
  Future<bool> updateProfile(Map<String, dynamic> data) async {
    saved.add(data);
    if (saveOk) state = AsyncData({...user, ...data});
    return saveOk;
  }
}

final _reminders = find.widgetWithText(SwitchListTile, 'Recordatorios de gastos fijos');
final _spending = find.widgetWithText(SwitchListTile, 'Alertas de gastos');

void main() {
  late MockNotificationRepository repo;

  Future<_FakeAuth> pumpScreen(
    WidgetTester tester, {
    bool enabled = true,
    bool spendingEnabled = true,
    bool saveOk = true,
  }) async {
    final auth = _FakeAuth({
      'id': 7,
      'recurring_reminders_enabled': enabled,
      'spending_alerts_enabled': spendingEnabled,
    }, saveOk: saveOk);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          notificationRepositoryProvider.overrideWithValue(repo),
          authProvider.overrideWith(() => auth),
        ],
        child: MaterialApp(
          theme: ThemeData(extensions: const [AppSemanticColors.light]),
          home: const NotificationsScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();
    return auth;
  }

  setUp(() {
    repo = MockNotificationRepository();
    when(repo.getUnreadCount()).thenAnswer((_) async => 0);
    when(repo.markAllRead()).thenAnswer((_) async {});
    when(repo.getNotifications()).thenAnswer((_) async => []);
  });

  testWidgets('sin avisos muestra el estado vacío', (tester) async {
    await pumpScreen(tester);

    expect(find.text('Sin notificaciones'), findsOneWidget);
  });

  testWidgets('muestra el historial con título y texto', (tester) async {
    when(repo.getNotifications()).thenAnswer((_) async => [
          {
            'id': 1,
            'type': 'recurring_reminder',
            'title': 'Gastos fijos por vencer',
            'body': 'En 3 días vence Alquiler.',
            'created_at': '2026-11-07T12:00:00Z',
            'read_at': null,
          },
        ]);

    await pumpScreen(tester);

    expect(find.text('Gastos fijos por vencer'), findsOneWidget);
    expect(find.text('En 3 días vence Alquiler.'), findsOneWidget);
  });

  testWidgets('el interruptor refleja la preferencia del perfil', (tester) async {
    await pumpScreen(tester, enabled: false);

    final toggle = tester.widget<SwitchListTile>(_reminders);
    expect(toggle.value, isFalse);
  });

  testWidgets('apagar el interruptor guarda la preferencia', (tester) async {
    final auth = await pumpScreen(tester);

    await tester.tap(_reminders);
    await tester.pumpAndSettle();

    expect(auth.saved, [
      {'recurring_reminders_enabled': false},
    ]);
    expect(tester.widget<SwitchListTile>(_reminders).value, isFalse);
  });

  testWidgets('si no se puede guardar avisa y deja el interruptor como estaba', (tester) async {
    await pumpScreen(tester, saveOk: false);

    await tester.tap(_reminders);
    await tester.pumpAndSettle();

    expect(find.text('No se pudo guardar la preferencia'), findsOneWidget);
    expect(tester.widget<SwitchListTile>(_reminders).value, isTrue);
  });

  testWidgets('el interruptor de alertas refleja su propia preferencia', (tester) async {
    await pumpScreen(tester, spendingEnabled: false);

    expect(tester.widget<SwitchListTile>(_spending).value, isFalse);
    expect(tester.widget<SwitchListTile>(_reminders).value, isTrue);
  });

  testWidgets('apagar las alertas de gastos guarda solo esa preferencia', (tester) async {
    final auth = await pumpScreen(tester);

    await tester.tap(_spending);
    await tester.pumpAndSettle();

    expect(auth.saved, [
      {'spending_alerts_enabled': false},
    ]);
    expect(tester.widget<SwitchListTile>(_reminders).value, isTrue);
  });
}
