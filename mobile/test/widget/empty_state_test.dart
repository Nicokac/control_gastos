import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/core/widgets/empty_state.dart';

void main() {
  group('EmptyState', () {
    testWidgets('muestra título e ícono', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icons.inbox,
            title: 'Sin datos',
          ),
        ),
      ));

      expect(find.text('Sin datos'), findsOneWidget);
      expect(find.byIcon(Icons.inbox), findsOneWidget);
    });

    testWidgets('muestra subtítulo cuando se provee', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icons.inbox,
            title: 'Sin datos',
            subtitle: 'Tocá + para agregar',
          ),
        ),
      ));

      expect(find.text('Tocá + para agregar'), findsOneWidget);
    });

    testWidgets('no muestra subtítulo cuando no se provee', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icons.inbox,
            title: 'Sin datos',
          ),
        ),
      ));

      expect(find.text('Tocá + para agregar'), findsNothing);
    });

    testWidgets('muestra botón de acción cuando se provee', (tester) async {
      bool tapped = false;
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icons.inbox,
            title: 'Sin datos',
            actionLabel: 'Agregar',
            onAction: () => tapped = true,
          ),
        ),
      ));

      expect(find.text('Agregar'), findsOneWidget);
      await tester.tap(find.text('Agregar'));
      expect(tapped, isTrue);
    });

    testWidgets('no muestra botón cuando no hay acción', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icons.inbox,
            title: 'Sin datos',
            actionLabel: 'Agregar',
          ),
        ),
      ));

      expect(find.byType(FilledButton), findsNothing);
    });
  });
}
