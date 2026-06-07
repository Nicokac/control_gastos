import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/auth_repository.dart';
import 'package:control_gastos_app/features/auth/providers/auth_provider.dart';
import 'package:control_gastos_app/features/auth/screens/login_screen.dart';

import 'login_screen_test.mocks.dart';

@GenerateMocks([AuthRepository])
void main() {
  late MockAuthRepository mockRepo;

  Widget buildLogin(MockAuthRepository repo) {
    final router = GoRouter(
      routes: [
        GoRoute(path: '/', builder: (_, _a) => const LoginScreen()),
        GoRoute(path: '/register', builder: (_, _a) => const Scaffold(body: Text('Register'))),
        GoRoute(path: '/dashboard', builder: (_, _a) => const Scaffold(body: Text('Dashboard'))),
      ],
    );

    return ProviderScope(
      overrides: [authRepositoryProvider.overrideWithValue(repo)],
      child: MaterialApp.router(routerConfig: router),
    );
  }

  setUp(() {
    mockRepo = MockAuthRepository();
    when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);
  });

  group('LoginScreen — validación de campos', () {
    testWidgets('muestra error si email está vacío', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Iniciar sesión'));
      await tester.pumpAndSettle();

      expect(find.text('Ingresá tu email o usuario'), findsOneWidget);
    });

    testWidgets('muestra error si contraseña está vacía', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField).first, 'test@test.com');
      await tester.tap(find.text('Iniciar sesión'));
      await tester.pumpAndSettle();

      expect(find.text('Ingresá tu contraseña'), findsOneWidget);
    });

    testWidgets('no muestra errores con campos completos', (tester) async {
      when(mockRepo.login(email: anyNamed('email'), password: anyNamed('password')))
          .thenAnswer((_) async => {});
      when(mockRepo.getProfile()).thenAnswer((_) async => {'id': 1, 'username': 'nico'});

      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextFormField).first, 'test@test.com');
      await tester.enterText(find.byType(TextFormField).last, '1234');
      await tester.tap(find.text('Iniciar sesión'));
      await tester.pump();

      expect(find.text('Ingresá tu email o usuario'), findsNothing);
      expect(find.text('Ingresá tu contraseña'), findsNothing);
    });
  });

  group('LoginScreen — toggle de contraseña', () {
    testWidgets('contraseña oculta por defecto', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      final textField = tester.widget<TextField>(
        find.descendant(
          of: find.byType(TextFormField).last,
          matching: find.byType(TextField),
        ),
      );
      expect(textField.obscureText, isTrue);
    });

    testWidgets('toggle muestra y oculta la contraseña', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.visibility));
      await tester.pump();

      final textField = tester.widget<TextField>(
        find.descendant(
          of: find.byType(TextFormField).last,
          matching: find.byType(TextField),
        ),
      );
      expect(textField.obscureText, isFalse);
    });
  });

  group('LoginScreen — contenido', () {
    testWidgets('muestra título de la app', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      expect(find.text('Control de Gastos'), findsOneWidget);
    });

    testWidgets('muestra link para crear cuenta', (tester) async {
      await tester.pumpWidget(buildLogin(mockRepo));
      await tester.pumpAndSettle();

      expect(find.textContaining('Crear cuenta'), findsOneWidget);
    });
  });
}
