import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:control_gastos_app/data/repositories/notification_repository.dart';
import 'package:control_gastos_app/data/services/push_notification_service.dart';

import 'push_notification_service_test.mocks.dart';

@GenerateMocks([FirebaseMessaging, NotificationRepository, NotificationSettings])
void main() {
  late MockFirebaseMessaging messaging;
  late MockNotificationRepository repository;
  late StreamController<String> registered;
  late PushNotificationService service;

  void givenPermission(AuthorizationStatus status) {
    final settings = MockNotificationSettings();
    when(settings.authorizationStatus).thenReturn(status);
    when(messaging.requestPermission()).thenAnswer((_) async => settings);
  }

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    messaging = MockFirebaseMessaging();
    repository = MockNotificationRepository();
    registered = StreamController<String>.broadcast();
    when(messaging.onRegistered).thenAnswer((_) => registered.stream);
    when(messaging.register()).thenAnswer((_) async {});
    when(messaging.unregister()).thenAnswer((_) async {});
    when(repository.registerToken(any)).thenAnswer((_) async {});
    when(repository.unregisterToken(any)).thenAnswer((_) async {});
    service = PushNotificationService(messaging, repository);
  });

  tearDown(() => registered.close());

  group('PushNotificationService — registerDevice', () {
    test('sin permiso no registra en Firebase ni en el backend', () async {
      givenPermission(AuthorizationStatus.denied);

      await service.registerDevice();

      verifyNever(messaging.register());
      verifyNever(repository.registerToken(any));
    });

    test('con permiso registra en Firebase', () async {
      givenPermission(AuthorizationStatus.authorized);

      await service.registerDevice();

      verify(messaging.register()).called(1);
    });

    test('al recibir el FID lo envía al backend y lo guarda', () async {
      givenPermission(AuthorizationStatus.authorized);

      await service.registerDevice();
      registered.add('fid-nuevo');
      await pumpEventQueue();

      verify(repository.registerToken('fid-nuevo')).called(1);
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('push_registered_fid'), 'fid-nuevo');
    });

    test('reenvía el FID guardado aunque Firebase no lo vuelva a emitir', () async {
      SharedPreferences.setMockInitialValues({'push_registered_fid': 'fid-guardado'});
      givenPermission(AuthorizationStatus.authorized);

      await service.registerDevice();

      verify(repository.registerToken('fid-guardado')).called(1);
    });

    test('sin red guarda el FID igual para reenviarlo después', () async {
      givenPermission(AuthorizationStatus.authorized);
      when(repository.registerToken(any)).thenThrow(Exception('sin red'));

      await service.registerDevice();
      registered.add('fid-sin-red');
      await pumpEventQueue();

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('push_registered_fid'), 'fid-sin-red');
    });
  });

  group('PushNotificationService — unregisterDevice', () {
    test('desactiva el FID guardado en el backend y lo borra', () async {
      SharedPreferences.setMockInitialValues({'push_registered_fid': 'fid-guardado'});

      await service.unregisterDevice();

      verify(repository.unregisterToken('fid-guardado')).called(1);
      verify(messaging.unregister()).called(1);
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('push_registered_fid'), isNull);
    });

    test('sin FID guardado solo se desregistra de Firebase', () async {
      await service.unregisterDevice();

      verifyNever(repository.unregisterToken(any));
      verify(messaging.unregister()).called(1);
    });

    test('después del logout deja de escuchar nuevos FID', () async {
      givenPermission(AuthorizationStatus.authorized);
      await service.registerDevice();

      await service.unregisterDevice();
      registered.add('fid-tardio');
      await pumpEventQueue();

      verifyNever(repository.registerToken('fid-tardio'));
    });
  });
}
