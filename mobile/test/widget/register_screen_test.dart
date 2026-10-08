import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:control_gastos_app/data/repositories/auth_repository.dart';
import 'package:control_gastos_app/features/auth/providers/auth_provider.dart';
import 'package:control_gastos_app/features/auth/screens/login_screen.dart';
import 'package:control_gastos_app/features/auth/screens/register_screen.dart';

import 'register_screen_test.mocks.dart';

@GenerateMocks([AuthRepository])
void main() {
  late MockAuthRepository mockRepo;

  Widget buildApp() {
    final router = GoRouter(
      initialLocation: '/login',
      routes: [
        GoRoute(path: '/login', builder: (_, _a) => const LoginScreen()),
        GoRoute(path: '/register', builder: (_, _a) => const RegisterScreen()),
        GoRoute(path: '/dashboard', builder: (_, _a) => const Scaffold(body: Text('Dashboard'))),
      ],
    );

    return ProviderScope(
      overrides: [authRepositoryProvider.overrideWithValue(mockRepo)],
      child: MaterialApp.router(routerConfig: router),
    );
  }

  setUp(() {
    mockRepo = MockAuthRepository();
    when(mockRepo.isLoggedIn()).thenAnswer((_) async => false);
  });

  group('RegisterScreen — navegación (DT-090)', () {
    testWidgets('muestra botón de volver cuando se llega desde login', (tester) async {
      await tester.pumpWidget(buildApp());
      await tester.pumpAndSettle();

      await tester.tap(find.textContaining('Crear cuenta'));
      await tester.pumpAndSettle();

      expect(find.text('Crear cuenta'), findsWidgets);
      expect(find.byType(BackButton), findsOneWidget);
    });

    testWidgets('el botón de volver regresa al login', (tester) async {
      await tester.pumpWidget(buildApp());
      await tester.pumpAndSettle();

      await tester.tap(find.textContaining('Crear cuenta'));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();

      expect(find.text('Control de Gastos'), findsOneWidget);
    });
  });

  group('RegisterScreen — toggle de contraseña (DT-090)', () {
    testWidgets('ambos campos de contraseña ocultan el texto por defecto', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: RegisterScreen())),
      );
      await tester.pumpAndSettle();

      final fields = tester.widgetList<TextField>(find.byType(TextField)).toList();
      final passwordField = fields[2];
      final password2Field = fields[3];

      expect(passwordField.obscureText, isTrue);
      expect(password2Field.obscureText, isTrue);
    });

    testWidgets('tocar el ícono de ver contraseña la muestra', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: RegisterScreen())),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.visibility).first);
      await tester.pump();

      final fields = tester.widgetList<TextField>(find.byType(TextField)).toList();
      expect(fields[2].obscureText, isFalse);
    });

    testWidgets('el segundo campo de contraseña tiene su propio toggle', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: RegisterScreen())),
      );
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.visibility), findsNWidgets(2));

      await tester.tap(find.byIcon(Icons.visibility).last);
      await tester.pump();

      final fields = tester.widgetList<TextField>(find.byType(TextField)).toList();
      expect(fields[2].obscureText, isTrue);
      expect(fields[3].obscureText, isFalse);
    });
  });
}
