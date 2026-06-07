import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/features/dashboard/widgets/balance_card.dart';

void main() {
  Widget buildCard({
    required String income,
    required String expenses,
    required String balance,
    VoidCallback? onTapIncome,
    VoidCallback? onTapExpenses,
  }) {
    return MaterialApp(
      home: Scaffold(
        body: BalanceCard(
          totalIncome: income,
          totalExpenses: expenses,
          balance: balance,
          onTapIncome: onTapIncome,
          onTapExpenses: onTapExpenses,
        ),
      ),
    );
  }

  group('BalanceCard', () {
    testWidgets('muestra balance positivo en verde', (tester) async {
      await tester.pumpWidget(buildCard(
        income: '100000.00',
        expenses: '50000.00',
        balance: '50000.00',
      ));

      final balanceText = find.textContaining('50.000');
      expect(balanceText, findsWidgets);

      final richText = tester.widget<Text>(balanceText.first);
      expect(richText.style?.color, equals(Colors.green[700]));
    });

    testWidgets('muestra balance negativo en rojo', (tester) async {
      await tester.pumpWidget(buildCard(
        income: '10000.00',
        expenses: '50000.00',
        balance: '-40000.00',
      ));

      final balanceText = find.textContaining('40.000');
      expect(balanceText, findsWidgets);

      final richText = tester.widget<Text>(balanceText.first);
      expect(richText.style?.color, equals(Colors.red[700]));
    });

    testWidgets('muestra labels de Ingresos y Gastos', (tester) async {
      await tester.pumpWidget(buildCard(
        income: '100000.00',
        expenses: '50000.00',
        balance: '50000.00',
      ));

      expect(find.text('Ingresos'), findsOneWidget);
      expect(find.text('Gastos'), findsOneWidget);
    });

    testWidgets('dispara onTapIncome al tocar ingresos', (tester) async {
      bool tapped = false;
      await tester.pumpWidget(buildCard(
        income: '100000.00',
        expenses: '50000.00',
        balance: '50000.00',
        onTapIncome: () => tapped = true,
      ));

      await tester.tap(find.text('Ingresos'));
      expect(tapped, isTrue);
    });

    testWidgets('dispara onTapExpenses al tocar gastos', (tester) async {
      bool tapped = false;
      await tester.pumpWidget(buildCard(
        income: '100000.00',
        expenses: '50000.00',
        balance: '50000.00',
        onTapExpenses: () => tapped = true,
      ));

      await tester.tap(find.text('Gastos'));
      expect(tapped, isTrue);
    });
  });
}
