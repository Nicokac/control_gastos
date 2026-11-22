import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/core/providers/amounts_visibility_provider.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/features/dashboard/widgets/monthly_insights_card.dart';

class _FixedVisibility extends AmountsVisibilityNotifier {
  _FixedVisibility(this.hidden);

  final bool hidden;

  @override
  bool build() => hidden;
}

const _insights = {
  'month': 10,
  'year': 2026,
  'label': 'Octubre',
  'items': [
    {
      'kind': 'best_month',
      'tone': 'positive',
      'text': 'Fue tu mejor mes de ahorro del año: ingresaste \$ 80.000 más de lo que gastaste.',
      'masked_text': 'Fue tu mejor mes de ahorro del año: ingresaste •••••• más de lo que gastaste.',
    },
    {
      'kind': 'category_up',
      'tone': 'warning',
      'text': 'Gastaste 50% más en Delivery que tu promedio de los últimos 6 meses (\$ 15.000 contra \$ 10.000).',
      'masked_text': 'Gastaste 50% más en Delivery que tu promedio de los últimos 6 meses (•••••• contra ••••••).',
    },
  ],
};

Future<void> _pump(WidgetTester tester, {bool hidden = false}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [amountsHiddenProvider.overrideWith(() => _FixedVisibility(hidden))],
      child: MaterialApp(
        theme: ThemeData(extensions: const [AppSemanticColors.light]),
        home: const Scaffold(body: MonthlyInsightsCard(insights: _insights)),
      ),
    ),
  );
}

void main() {
  testWidgets('muestra el título con el mes y cada observación', (tester) async {
    await _pump(tester);

    expect(find.text('Tu octubre en resumen'), findsOneWidget);
    expect(find.textContaining('mejor mes de ahorro'), findsOneWidget);
    expect(find.textContaining('\$ 15.000'), findsOneWidget);
    expect(find.textContaining('\$ 15.000'), findsNothing);
  });

  testWidgets('el ícono depende del tono', (tester) async {
    await _pump(tester);

    expect(find.byIcon(Icons.check_circle_outline), findsOneWidget);
    expect(find.byIcon(Icons.arrow_circle_up), findsOneWidget);
  });

  testWidgets('con los montos ocultos usa el texto enmascarado', (tester) async {
    await _pump(tester, hidden: true);

    expect(find.textContaining('15.000'), findsNothing);
    expect(find.textContaining('(•••••• contra ••••••)'), findsOneWidget);
    expect(find.textContaining('Delivery'), findsOneWidget);
  });
}
