import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/core/providers/amounts_visibility_provider.dart';
import 'package:control_gastos_app/core/theme/app_semantic_colors.dart';
import 'package:control_gastos_app/core/utils/formatters.dart';
import 'package:control_gastos_app/features/dashboard/widgets/projection_banner.dart';

class _FixedVisibility extends AmountsVisibilityNotifier {
  _FixedVisibility(this.hidden);

  final bool hidden;

  @override
  bool build() => hidden;
}

Future<void> _pumpBanner(
  WidgetTester tester, {
  double width = 360,
  double textScale = 1.0,
  bool hidden = false,
}) async {
  tester.view.physicalSize = Size(width * 3, 800 * 3);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        amountsHiddenProvider.overrideWith(() => _FixedVisibility(hidden)),
      ],
      child: MaterialApp(
        theme: ThemeData(extensions: const [AppSemanticColors.light]),
        home: MediaQuery(
          data: MediaQueryData(
            size: Size(width, 800),
            textScaler: TextScaler.linear(textScale),
          ),
          child: const Scaffold(
            body: Padding(
              padding: EdgeInsets.all(16),
              child: ProjectionBanner(
                projectedExpense: '1234567.89',
                projectedBalance: '-250000.00',
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

void main() {
  group('ProjectionBanner (DT-107)', () {
    final expenseText =
        'Proyección al cierre: ${formatArsString('1234567.89').replaceAll(' ', ' ')} en gastos';

    for (final scale in [1.0, 1.3]) {
      testWidgets(
        'a 360 dp y fuente x$scale no se desborda y muestra el monto',
        (tester) async {
          await _pumpBanner(tester, textScale: scale);

          expect(tester.takeException(), isNull);
          expect(find.text(expenseText), findsOneWidget);
          expect(find.text(formatArsString('-250000.00')), findsOneWidget);
        },
      );
    }

    testWidgets('con montos ocultos no muestra las cifras', (tester) async {
      await _pumpBanner(tester, hidden: true);

      expect(
        find.text('Proyección al cierre: •••••• en gastos'),
        findsOneWidget,
      );
      expect(find.text(formatArsString('-250000.00')), findsNothing);
      expect(find.text('••••••'), findsOneWidget);
    });
  });
}
