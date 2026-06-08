import 'package:intl/intl.dart';

String formatArs(double value) {
  final formatted = NumberFormat('#,##0.##', 'es_AR').format(value);
  return '\$ $formatted';
}

String formatArsString(String raw) {
  return formatArs(double.tryParse(raw) ?? 0);
}

// Convierte input del usuario en formato argentino (1.234,56) a double.
// Elimina puntos de miles y reemplaza coma decimal por punto.
double? parseArgentineAmount(String input) {
  final normalized = input.replaceAll('.', '').replaceAll(',', '.');
  return double.tryParse(normalized);
}
