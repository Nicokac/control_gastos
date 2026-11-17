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

// Monto que devuelve la API ("8500.00") al formato que lee parseArgentineAmount
// ("8500" o "1500,50"): pasado tal cual, el punto decimal se tomaría como de miles.
String apiAmountToInput(String apiAmount) {
  final value = double.tryParse(apiAmount);
  if (value == null) return apiAmount;
  if (value == value.truncateToDouble()) return value.toStringAsFixed(0);
  return value.toStringAsFixed(2).replaceAll('.', ',');
}
