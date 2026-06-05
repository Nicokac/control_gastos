import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../core/utils/formatters.dart';

class ExpenseChart extends StatelessWidget {
  final List<dynamic> expensesByCategory;

  const ExpenseChart({super.key, required this.expensesByCategory});

  @override
  Widget build(BuildContext context) {
    if (expensesByCategory.isEmpty) {
      return Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: const Padding(
          padding: EdgeInsets.all(24),
          child: Center(
            child: Text(
              'Sin gastos este mes',
              style: TextStyle(color: Colors.grey),
            ),
          ),
        ),
      );
    }

    final total = expensesByCategory.fold<double>(
      0,
      (sum, e) => sum + (double.tryParse(e['total'] as String) ?? 0),
    );

    final segments = expensesByCategory.map((e) {
      return _Segment(
        label: e['category_name'] as String,
        value: double.tryParse(e['total'] as String) ?? 0,
        color: _parseColor(e['category_color'] as String? ?? '#6c757d'),
      );
    }).toList();

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Gastos por categoría',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 20),
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                SizedBox(
                  width: 120,
                  height: 120,
                  child: CustomPaint(
                    painter: _PieChartPainter(segments: segments),
                  ),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    children: segments.map((s) {
                      final pct = total > 0 ? (s.value / total * 100) : 0;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          children: [
                            Container(
                              width: 10,
                              height: 10,
                              decoration: BoxDecoration(
                                color: s.color,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                s.label,
                                style: const TextStyle(fontSize: 12),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Text(
                              '${pct.toStringAsFixed(0)}%',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              'Total: ${_formatAmount(total)}',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatAmount(double value) => formatArs(value);

  Color _parseColor(String hex) {
    final clean = hex.replaceFirst('#', '');
    return Color(int.parse('FF$clean', radix: 16));
  }
}

class _Segment {
  final String label;
  final double value;
  final Color color;
  const _Segment({required this.label, required this.value, required this.color});
}

class _PieChartPainter extends CustomPainter {
  final List<_Segment> segments;
  _PieChartPainter({required this.segments});

  @override
  void paint(Canvas canvas, Size size) {
    final total = segments.fold<double>(0, (s, e) => s + e.value);
    if (total == 0) return;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);

    double startAngle = -math.pi / 2;
    for (final seg in segments) {
      final sweep = (seg.value / total) * 2 * math.pi;
      final paint = Paint()
        ..color = seg.color
        ..style = PaintingStyle.fill;
      canvas.drawArc(rect, startAngle, sweep, true, paint);
      startAngle += sweep;
    }

    // hole interior
    final holePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, radius * 0.52, holePaint);
  }

  @override
  bool shouldRepaint(_PieChartPainter old) => old.segments != segments;
}
