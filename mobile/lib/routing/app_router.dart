import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/screens/splash_screen.dart';
import '../features/auth/screens/login_screen.dart';
import '../features/auth/screens/register_screen.dart';
import '../features/dashboard/screens/dashboard_screen.dart';
import '../features/expenses/screens/expense_list_screen.dart';
import '../features/expenses/screens/expense_form_screen.dart';
import '../features/income/screens/income_list_screen.dart';
import '../features/income/screens/income_form_screen.dart';
import '../features/shared_expenses/screens/shared_expense_list_screen.dart';
import '../features/shared_expenses/screens/shared_expense_form_screen.dart';
import '../features/shared_expenses/screens/household_members_screen.dart';
import '../features/settings/screens/settings_screen.dart';
import '../features/auth/providers/auth_provider.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      if (authState.isLoading) return null;

      final isLoggedIn = authState.valueOrNull != null;
      final location = state.matchedLocation;
      final onSplash = location == '/splash';
      final onAuth = location == '/login' || location == '/register';

      if (onSplash) {
        return isLoggedIn ? '/dashboard' : '/login';
      }
      if (!isLoggedIn && !onAuth) return '/login';
      if (isLoggedIn && onAuth) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, s) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, s) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, s) => const RegisterScreen()),
      GoRoute(path: '/dashboard', builder: (_, s) => const DashboardScreen()),
      GoRoute(
        path: '/expenses',
        builder: (_, s) => const ExpenseListScreen(),
      ),
      GoRoute(
        path: '/expenses/new',
        builder: (_, s) => const ExpenseFormScreen(),
      ),
      GoRoute(
        path: '/expenses/edit/:id',
        builder: (_, state) => ExpenseFormScreen(
          existing: state.extra as Map<String, dynamic>?,
        ),
      ),
      GoRoute(
        path: '/income',
        builder: (_, s) => const IncomeListScreen(),
      ),
      GoRoute(
        path: '/income/new',
        builder: (_, s) => const IncomeFormScreen(),
      ),
      GoRoute(
        path: '/income/edit/:id',
        builder: (_, state) => IncomeFormScreen(
          existing: state.extra as Map<String, dynamic>?,
        ),
      ),
      GoRoute(
        path: '/shared-expenses',
        builder: (_, s) => const SharedExpenseListScreen(),
      ),
      GoRoute(
        path: '/shared-expenses/new',
        builder: (_, s) => const SharedExpenseFormScreen(),
      ),
      GoRoute(
        path: '/shared-expenses/edit/:id',
        builder: (_, state) => SharedExpenseFormScreen(
          existing: state.extra as Map<String, dynamic>?,
        ),
      ),
      GoRoute(
        path: '/shared-expenses/members',
        builder: (_, s) => const HouseholdMembersScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (_, s) => const SettingsScreen(),
      ),
    ],
  );
});
