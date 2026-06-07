import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/features/dashboard/widgets/pending_recurring_card.dart';

void main() {
  Widget buildCard({
    required List<dynamic> pending,
    required int totalRecurring,
    VoidCallback? onViewAll,
  }) {
    return MaterialApp(
      home: Scaffold(
        body: PendingRecurringCard(
          pending: pending,
          totalRecurring: totalRecurring,
          onViewAll: onViewAll,
        ),
      ),
    );
  }

  group('PendingRecurringCard — todos pagados', () {
    testWidgets('muestra ícono verde cuando no hay pendientes', (tester) async {
      await tester.pumpWidget(buildCard(pending: [], totalRecurring: 5));

      expect(find.byIcon(Icons.check_circle_outline), findsWidgets);
      expect(find.byIcon(Icons.warning_amber_rounded), findsNothing);
    });

    testWidgets('muestra 5 de 5 pagados', (tester) async {
      await tester.pumpWidget(buildCard(pending: [], totalRecurring: 5));

      expect(find.textContaining('5 de 5'), findsOneWidget);
    });
  });

  group('PendingRecurringCard — con pendientes', () {
    final pending = [
      {'id': 1, 'name': 'Flow', 'status': 'pending', 'last_amount': '5000.00'},
      {'id': 2, 'name': 'Pilates', 'status': 'overdue', 'last_amount': '3000.00'},
    ];

    testWidgets('muestra ícono naranja de advertencia', (tester) async {
      await tester.pumpWidget(buildCard(pending: pending, totalRecurring: 5));

      expect(find.byIcon(Icons.warning_amber_rounded), findsOneWidget);
    });

    testWidgets('muestra chip de pendientes', (tester) async {
      await tester.pumpWidget(buildCard(pending: pending, totalRecurring: 5));

      expect(find.textContaining('pendiente'), findsWidgets);
    });

    testWidgets('muestra chip de vencidos', (tester) async {
      await tester.pumpWidget(buildCard(pending: pending, totalRecurring: 5));

      expect(find.textContaining('vencido'), findsWidgets);
    });

    testWidgets('muestra los nombres de los recurrentes pendientes', (tester) async {
      await tester.pumpWidget(buildCard(pending: pending, totalRecurring: 5));

      expect(find.text('Flow'), findsOneWidget);
      expect(find.text('Pilates'), findsOneWidget);
    });
  });

  group('PendingRecurringCard — botón Ver todos', () {
    testWidgets('muestra Ver todos cuando se provee onViewAll', (tester) async {
      await tester.pumpWidget(buildCard(
        pending: [],
        totalRecurring: 3,
        onViewAll: () {},
      ));

      expect(find.text('Ver todos'), findsOneWidget);
    });

    testWidgets('dispara onViewAll al tocar', (tester) async {
      bool tapped = false;
      await tester.pumpWidget(buildCard(
        pending: [],
        totalRecurring: 3,
        onViewAll: () => tapped = true,
      ));

      await tester.tap(find.text('Ver todos'));
      expect(tapped, isTrue);
    });
  });
}
