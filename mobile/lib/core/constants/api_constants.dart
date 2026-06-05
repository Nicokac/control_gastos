class ApiConstants {
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';

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
