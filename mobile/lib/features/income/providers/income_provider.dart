import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/income_repository.dart';
import '../../dashboard/providers/dashboard_provider.dart';

final incomeRepositoryProvider = Provider<IncomeRepository>((ref) {
  return IncomeRepository();
});

class IncomeListNotifier extends AsyncNotifier<List<dynamic>> {
  int _month = DateTime.now().month;
  int _year = DateTime.now().year;

  @override
  Future<List<dynamic>> build() => _fetch();

  Future<List<dynamic>> _fetch() {
    return ref
        .read(incomeRepositoryProvider)
        .getIncome(month: _month, year: _year);
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
      await ref.read(incomeRepositoryProvider).createIncome(data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> editIncome(int id, Map<String, dynamic> data) async {
    try {
      await ref.read(incomeRepositoryProvider).updateIncome(id, data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> delete(int id) async {
    try {
      await ref.read(incomeRepositoryProvider).deleteIncome(id);
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

final incomeListProvider =
    AsyncNotifierProvider<IncomeListNotifier, List<dynamic>>(
  IncomeListNotifier.new,
);

final incomeCategoriesProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(incomeRepositoryProvider).getCategories();
});
