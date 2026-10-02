class ApiConstants {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://control-gastos-fr8z.onrender.com/api/v1',
  );

  static const String appVersion = '1.16.0'; // mantener sincronizado con pubspec.yaml
  // Resumen de novedades de la versión actual (DT-068) — actualizar junto con appVersion.
  static const String latestReleaseSummary =
      'Mejoras de categorías en Ingresos y Gastos, y correcciones varias.';
  static const String websiteUrl = 'https://control-gastos-fr8z.onrender.com';
  static const String developerName = 'Nicolás Kachuk';
  static const String developerEmail = 'kachuknm@gmail.com';
  static const String cafesitoUrl = 'https://cafecito.app/niicok';

  static const String tokenObtain = '/auth/token/';
  static const String tokenRefresh = '/auth/token/refresh/';
  static const String register = '/auth/register/';
  static const String me = '/auth/me/';

  static const String categories = '/categories/';
  static const String expenses = '/expenses/';
  static const String income = '/income/';
  static const String savings = '/savings/';
  static const String recurring = '/recurring/';
  static const String recurringIncome = '/recurring-income/';
  static const String sharedExpenses = '/shared-expenses/';
  static const String householdMembers = '/household-members/';
  static const String dashboard = '/dashboard/';
}
