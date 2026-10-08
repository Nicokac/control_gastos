/// Radios de borde estándar de la app. Usar siempre estos valores en vez de
/// hardcodear BorderRadius.circular(N) para mantener un criterio consistente.
class AppRadius {
  /// Cards, contenedores de listas, tiles con fondo propio.
  static const double card = 16;

  /// Elementos chicos dentro de un card (badges, chips, botones pequeños).
  static const double small = 8;

  AppRadius._();
}
