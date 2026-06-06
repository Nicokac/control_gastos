import 'package:flutter/material.dart';
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
import '../features/categories/screens/categories_screen.dart';
import '../features/recurring/screens/recurring_list_screen.dart';
import '../features/recurring/screens/recurring_form_screen.dart';
import '../features/savings/screens/savings_list_screen.dart';
import '../features/savings/screens/saving_form_screen.dart';
import '../features/savings/screens/saving_detail_screen.dart';
import '../features/auth/providers/auth_provider.dart';

CustomTransitionPage<T> _buildPage<T>({
  required BuildContext context,
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<T>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 220),
    reverseTransitionDuration: const Duration(milliseconds: 180),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final fadeAnim = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOut,
      );
      final slideAnim = Tween<Offset>(
        begin: const Offset(0.04, 0),
        end: Offset.zero,
      ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut));

      return FadeTransition(
        opacity: fadeAnim,
        child: SlideTransition(position: slideAnim, child: child),
      );
    },
  );
}

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
      GoRoute(
        path: '/splash',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const SplashScreen()),
      ),
      GoRoute(
        path: '/login',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const LoginScreen()),
      ),
      GoRoute(
        path: '/register',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const RegisterScreen()),
      ),
      GoRoute(
        path: '/dashboard',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const DashboardScreen()),
      ),
      GoRoute(
        path: '/expenses',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const ExpenseListScreen()),
      ),
      GoRoute(
        path: '/expenses/new',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const ExpenseFormScreen()),
      ),
      GoRoute(
        path: '/expenses/edit/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: ExpenseFormScreen(existing: s.extra as Map<String, dynamic>?),
        ),
      ),
      GoRoute(
        path: '/income',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const IncomeListScreen()),
      ),
      GoRoute(
        path: '/income/new',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const IncomeFormScreen()),
      ),
      GoRoute(
        path: '/income/edit/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: IncomeFormScreen(existing: s.extra as Map<String, dynamic>?),
        ),
      ),
      GoRoute(
        path: '/shared-expenses',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: const SharedExpenseListScreen(),
        ),
      ),
      GoRoute(
        path: '/shared-expenses/new',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: const SharedExpenseFormScreen(),
        ),
      ),
      GoRoute(
        path: '/shared-expenses/edit/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: SharedExpenseFormScreen(
            existing: s.extra as Map<String, dynamic>?,
          ),
        ),
      ),
      GoRoute(
        path: '/shared-expenses/members',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: const HouseholdMembersScreen(),
        ),
      ),
      GoRoute(
        path: '/settings',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const SettingsScreen()),
      ),
      GoRoute(
        path: '/categories',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const CategoriesScreen()),
      ),
      GoRoute(
        path: '/recurring',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: const RecurringListScreen(),
        ),
      ),
      GoRoute(
        path: '/recurring/new',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: const RecurringFormScreen(),
        ),
      ),
      GoRoute(
        path: '/recurring/edit/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: RecurringFormScreen(
            existing: s.extra as Map<String, dynamic>?,
          ),
        ),
      ),
      GoRoute(
        path: '/savings',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const SavingsListScreen()),
      ),
      GoRoute(
        path: '/savings/new',
        pageBuilder: (c, s) =>
            _buildPage(context: c, state: s, child: const SavingFormScreen()),
      ),
      GoRoute(
        path: '/savings/edit/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: SavingFormScreen(existing: s.extra as Map<String, dynamic>?),
        ),
      ),
      GoRoute(
        path: '/savings/:id',
        pageBuilder: (c, s) => _buildPage(
          context: c,
          state: s,
          child: SavingDetailScreen(saving: s.extra as Map<String, dynamic>),
        ),
      ),
    ],
  );
});
