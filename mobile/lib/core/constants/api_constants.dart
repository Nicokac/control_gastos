class ApiConstants {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://control-gastos-fr8z.onrender.com/api/v1',
  );

  // Resumen de novedades de la versión actual (DT-068) — actualizar junto con el bump de pubspec.yaml.
  static const String latestReleaseSummary =
      'Mejoras para pantallas chicas y letra grande: los accesos del inicio y la proyección del mes ya no se cortan, y elegir el día de vencimiento de un gasto fijo es más cómodo.';
  static const String websiteUrl = 'https://controldegastos.ar';
  static const String termsUrl =
      'https://controldegastos.ar/terms/';
  static const String privacyUrl =
      'https://controldegastos.ar/privacy/';
  static const String developerName = 'Nicolás Kachuk';
  static const String developerEmail = 'contacto@controldegastos.ar';
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
  static const String notifications = '/notifications/';
  static const String notificationsUnreadCount = '/notifications/unread-count/';
  static const String notificationsMarkRead = '/notifications/mark-read/';
  static const String deviceToken = '/notifications/device-token/';
}
