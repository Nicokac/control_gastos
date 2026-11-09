import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:control_gastos_app/features/dashboard/widgets/dashboard_shortcut_button.dart';

Future<void> _pumpShortcuts(
  WidgetTester tester, {
  double width = 360,
  double textScale = 1.0,
}) async {
  tester.view.physicalSize = Size(width * 3, 800 * 3);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(
          size: Size(width, 800),
          textScaler: TextScaler.linear(textScale),
        ),
        child: Scaffold(
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                for (final label in [
                  'Compartidos',
                  'Ahorros',
                  'Categorías',
                ]) ...[
                  if (label != 'Compartidos') const SizedBox(width: 8),
                  Expanded(
                    child: DashboardShortcutButton(
                      icon: Icons.people,
                      label: label,
                      color: Colors.blue,
                      onPressed: () {},
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

/// Con maxLines: 1, un texto que no entra se corta: si alguno excede su línea, el arreglo se perdió.
bool _anyLabelTruncated(WidgetTester tester) => tester
    .renderObjectList<RenderParagraph>(find.byType(RichText))
    .any((paragraph) => paragraph.didExceedMaxLines);

void main() {
  group('DashboardShortcutButton (DT-103)', () {
    for (final (width, scale) in [(360.0, 1.0), (360.0, 1.3), (411.0, 1.0)]) {
      testWidgets(
        'ningún texto se corta ni se parte a ${width.toInt()} dp y fuente x$scale',
        (tester) async {
          await _pumpShortcuts(tester, width: width, textScale: scale);

          expect(_anyLabelTruncated(tester), isFalse);
          expect(tester.takeException(), isNull);
        },
      );
    }

    testWidgets('tocar el botón ejecuta la acción', (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DashboardShortcutButton(
              icon: Icons.people,
              label: 'Compartidos',
              color: Colors.blue,
              onPressed: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Compartidos'));

      expect(tapped, isTrue);
    });
  });
}
