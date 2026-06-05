import 'package:intl/intl.dart';

String formatArs(double value) {
  final formatted = NumberFormat('#,##0', 'es_AR').format(value);
  return '\$ $formatted';
}

String formatArsString(String raw) {
  return formatArs(double.tryParse(raw) ?? 0);
}
