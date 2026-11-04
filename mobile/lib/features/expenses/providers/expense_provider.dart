import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/expense_repository.dart';
import '../../dashboard/providers/dashboard_provider.dart';

final expenseRepositoryProvider = Provider<ExpenseRepository>((ref) {
  return ExpenseRepository();
});

class ExpenseListNotifier extends AsyncNotifier<List<dynamic>> {
  int _month = DateTime.now().month;
  int _year = DateTime.now().year;

  @override
  Future<List<dynamic>> build() => _fetch();

  Future<List<dynamic>> _fetch() {
    return ref
        .read(expenseRepositoryProvider)
        .getExpenses(month: _month, year: _year);
  }

  Future<void> setMonth(int month, int year) async {
    _month = month;
    _year = year;
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<bool> create(Map<String, dynamic> data) async {
    try {
      await ref.read(expenseRepositoryProvider).createExpense(data);
      unawaited(_reloadAfterPop());
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> editExpense(int id, Map<String, dynamic> data) async {
    try {
      await ref.read(expenseRepositoryProvider).updateExpense(id, data);
      unawaited(_reloadAfterPop());
      return true;
    } catch (_) {
      return false;
    }
  }

  // Diferido al próximo microtask: evita reconstruir la pantalla mientras
  // el caller todavía está cerrando el formulario/modal actual (DT-098).
  Future<void> _reloadAfterPop() async {
    await Future<void>.delayed(Duration.zero);
    await reload();
    ref.invalidate(dashboardProvider);
  }

  Future<bool> delete(int id) async {
    try {
      await ref.read(expenseRepositoryProvider).deleteExpense(id);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  int get currentMonth => _month;
  int get currentYear => _year;
}

final expenseListProvider =
    AsyncNotifierProvider<ExpenseListNotifier, List<dynamic>>(
  ExpenseListNotifier.new,
);

// Categorías — se cargan una vez y se cachean
final categoriesProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(expenseRepositoryProvider).getCategories();
});
