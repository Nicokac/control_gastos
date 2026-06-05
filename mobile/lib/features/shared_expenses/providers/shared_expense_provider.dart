import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/shared_expense_repository.dart';
import '../../dashboard/providers/dashboard_provider.dart';

final sharedExpenseRepositoryProvider =
    Provider<SharedExpenseRepository>((ref) {
  return SharedExpenseRepository();
});

class SharedExpenseListNotifier extends AsyncNotifier<List<dynamic>> {
  int _month = DateTime.now().month;
  int _year = DateTime.now().year;

  @override
  Future<List<dynamic>> build() => _fetch();

  Future<List<dynamic>> _fetch() {
    return ref
        .read(sharedExpenseRepositoryProvider)
        .getSharedExpenses(month: _month, year: _year);
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
      await ref.read(sharedExpenseRepositoryProvider).createSharedExpense(data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> editExpense(int id, Map<String, dynamic> data) async {
    try {
      await ref
          .read(sharedExpenseRepositoryProvider)
          .updateSharedExpense(id, data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> delete(int id) async {
    try {
      await ref.read(sharedExpenseRepositoryProvider).deleteSharedExpense(id);
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

final sharedExpenseListProvider =
    AsyncNotifierProvider<SharedExpenseListNotifier, List<dynamic>>(
  SharedExpenseListNotifier.new,
);

final householdMembersProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(sharedExpenseRepositoryProvider).getMembers();
});

final sharedCategoriesProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(sharedExpenseRepositoryProvider).getCategories();
});
