import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/dashboard_repository.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository();
});

class DashboardNotifier
    extends AsyncNotifier<Map<String, dynamic>> {
  int _month = DateTime.now().month;
  int _year = DateTime.now().year;

  @override
  Future<Map<String, dynamic>> build() async {
    return _fetch();
  }

  Future<Map<String, dynamic>> _fetch() {
    final repo = ref.read(dashboardRepositoryProvider);
    return repo.getDashboard(month: _month, year: _year);
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<void> setMonth(int month, int year) async {
    _month = month;
    _year = year;
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  int get currentMonth => _month;
  int get currentYear => _year;
}

final dashboardProvider =
    AsyncNotifierProvider<DashboardNotifier, Map<String, dynamic>>(
  DashboardNotifier.new,
);
