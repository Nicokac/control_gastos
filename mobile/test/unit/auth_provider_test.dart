import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/auth_repository.dart';
import 'package:control_gastos_app/features/auth/providers/auth_provider.dart';

import 'auth_provider_test.mocks.dart';

@GenerateMocks([AuthRepository])
void main() {
  late MockAuthRepository mockRepo;
  late ProviderContainer container;

  setUp(() {
    mockRepo = MockAuthRepository();
    container = ProviderContainer(
      overrides: [
        authRepositoryProvider.overrideWithValue(mockRepo),
      ],
    );
  });

  tearDown(() => container.dispose());

  group('AuthNotifier — build', () {
    test('retorna null si no está logueado', () async {
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);

      final result = await container.read(authProvider.future);
      expect(result, isNull);
    });

    test('retorna el perfil si está logueado', () async {
      final profile = {'id': 1, 'username': 'nicolas', 'email': 'test@test.com'};
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => true);
      when(mockRepo.getProfile()).thenAnswer((_) async => profile);

      final result = await container.read(authProvider.future);
      expect(result, equals(profile));
    });
  });

  group('AuthNotifier — login', () {
    test('login exitoso actualiza el estado con el perfil', () async {
      final profile = {'id': 1, 'username': 'nicolas'};
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);
      when(mockRepo.login(email: 'nicolas@test.com', password: '1234'))
          .thenAnswer((_) async => {});
      when(mockRepo.getProfile()).thenAnswer((_) async => profile);

      await container.read(authProvider.future);
      final notifier = container.read(authProvider.notifier);
      final error = await notifier.login(email: 'nicolas@test.com', password: '1234');

      expect(error, isNull);
      expect(container.read(authProvider).valueOrNull, equals(profile));
    });

    test('login fallido con 401 retorna mensaje de error', () async {
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);
      when(mockRepo.login(email: anyNamed('email'), password: anyNamed('password')))
          .thenThrow(Exception('401 Unauthorized'));

      await container.read(authProvider.future);
      final notifier = container.read(authProvider.notifier);
      final error = await notifier.login(email: 'mal@test.com', password: 'wrong');

      expect(error, contains('incorrectos'));
      expect(container.read(authProvider).valueOrNull, isNull);
    });

    test('login fallido por conexión retorna mensaje de red', () async {
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);
      when(mockRepo.login(email: anyNamed('email'), password: anyNamed('password')))
          .thenThrow(Exception('SocketException: connection refused'));

      await container.read(authProvider.future);
      final notifier = container.read(authProvider.notifier);
      final error = await notifier.login(email: 'a@b.com', password: '1234');

      expect(error, contains('servidor'));
    });
  });

  group('AuthNotifier — logout', () {
    test('logout limpia el estado', () async {
      final profile = {'id': 1, 'username': 'nicolas'};
      when(mockRepo.isLoggedIn()).thenAnswer((_) async => true);
      when(mockRepo.getProfile()).thenAnswer((_) async => profile);
      when(mockRepo.logout()).thenAnswer((_) async => {});

      await container.read(authProvider.future);
      final notifier = container.read(authProvider.notifier);
      await notifier.logout();

      expect(container.read(authProvider).valueOrNull, isNull);
    });
  });
}
