import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/features/dashboard/widgets/dashboard_skeleton.dart';

void main() {
  group('DashboardSkeleton', () {
    testWidgets('renderiza sin errores', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: DashboardSkeleton()),
      ));

      expect(find.byType(DashboardSkeleton), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('contiene un ListView', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: DashboardSkeleton()),
      ));

      expect(find.byType(ListView), findsOneWidget);
    });

    testWidgets('contiene múltiples Cards de placeholder', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: DashboardSkeleton()),
      ));

      expect(find.byType(Card), findsWidgets);
    });
  });
}
