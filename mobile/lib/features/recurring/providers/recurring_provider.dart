import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/recurring_repository.dart';
import '../../dashboard/providers/dashboard_provider.dart';

final recurringRepositoryProvider = Provider<RecurringRepository>((ref) {
  return RecurringRepository();
});

class RecurringListNotifier extends AsyncNotifier<List<dynamic>> {
  @override
  Future<List<dynamic>> build() => _fetch();

  Future<List<dynamic>> _fetch() {
    return ref.read(recurringRepositoryProvider).getRecurring();
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<bool> create(Map<String, dynamic> data) async {
    try {
      await ref.read(recurringRepositoryProvider).createRecurring(data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> editRecurring(int id, Map<String, dynamic> data) async {
    try {
      await ref.read(recurringRepositoryProvider).updateRecurring(id, data);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> delete(int id) async {
    try {
      await ref.read(recurringRepositoryProvider).deleteRecurring(id);
      await reload();
      ref.invalidate(dashboardProvider);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<String?> unmarkPaid(int id) async {
    try {
      await ref.read(recurringRepositoryProvider).unmarkPaid(id);
      await reload();
      ref.invalidate(dashboardProvider);
      return null;
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('No hay pago')) return 'No hay pago registrado este mes';
      return 'Error al revertir el pago';
    }
  }

  Future<String?> markPaid(int id, {double? amount}) async {
    try {
      await ref.read(recurringRepositoryProvider).markPaid(id, amount: amount);
      await reload();
      ref.invalidate(dashboardProvider);
      return null;
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('ya fue registrado')) {
        return 'Este gasto ya fue registrado este mes';
      }
      return 'Error al registrar el pago';
    }
  }
}

final recurringListProvider =
    AsyncNotifierProvider<RecurringListNotifier, List<dynamic>>(
  RecurringListNotifier.new,
);

final recurringCategoriesProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(recurringRepositoryProvider).getCategories();
});
