class ApiConstants {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://control-gastos-fr8z.onrender.com/api/v1',
  );

  // Resumen de novedades de la versión actual (DT-068) — actualizar junto con el bump de pubspec.yaml.
  static const String latestReleaseSummary =
      'Nuevo: si te sobró plata al cerrar el mes, te lo mostramos en el dashboard para destinarlo a una meta de ahorro.';
  static const String websiteUrl = 'https://control-gastos-fr8z.onrender.com';
  static const String termsUrl =
      'https://control-gastos-fr8z.onrender.com/terms/';
  static const String privacyUrl =
      'https://control-gastos-fr8z.onrender.com/privacy/';
  static const String developerName = 'Nicolás Kachuk';
  static const String developerEmail = 'kachuknm@gmail.com';
  static const String cafesitoUrl = 'https://cafecito.app/niicok';

  static const String tokenObtain = '/auth/token/';
  static const String tokenRefresh = '/auth/token/refresh/';
  static const String register = '/auth/register/';
  static const String me = '/auth/me/';
  static const String passwordResetRequest = '/auth/password/reset/';
  static const String passwordResetConfirm = '/auth/password/reset/confirm/';

  static const String categories = '/categories/';
  static const String expenses = '/expenses/';
  static const String income = '/income/';
  static const String savings = '/savings/';
  static const String rolloverSuggestions = '/rollover-suggestions/';
  static const String recurring = '/recurring/';
  static const String recurringIncome = '/recurring-income/';
  static const String sharedExpenses = '/shared-expenses/';
  static const String householdMembers = '/household-members/';
  static const String dashboard = '/dashboard/';
  static const String feedback = '/feedback/';
}
