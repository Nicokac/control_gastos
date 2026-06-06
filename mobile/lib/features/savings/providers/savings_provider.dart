import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/savings_repository.dart';
import '../../dashboard/providers/dashboard_provider.dart';

final savingsRepositoryProvider = Provider<SavingsRepository>((ref) {
  return SavingsRepository();
});

String? _errorDetail(Object e) {
  if (e is DioException) {
    final data = e.response?.data;
    if (data is Map && data['detail'] is String)
      return data['detail'] as String;
  }
  return null;
}

class SavingsListNotifier extends AsyncNotifier<List<dynamic>> {
  @override
  Future<List<dynamic>> build() => _fetch();

  Future<List<dynamic>> _fetch() {
    return ref.read(savingsRepositoryProvider).getSavings();
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<bool> create(Map<String, dynamic> data) async {
    try {
      await ref.read(savingsRepositoryProvider).createSaving(data);
      await reload();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> editSaving(int id, Map<String, dynamic> data) async {
    try {
      await ref.read(savingsRepositoryProvider).updateSaving(id, data);
      await reload();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> delete(int id) async {
    try {
      await ref.read(savingsRepositoryProvider).deleteSaving(id);
      await reload();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<String?> deposit(int id, double amount, String description) async {
    try {
      await ref
          .read(savingsRepositoryProvider)
          .deposit(id, amount, description);
      await reload();
      ref.invalidate(dashboardProvider);
      return null;
    } catch (e) {
      return _errorDetail(e) ?? 'Error al registrar el depósito';
    }
  }

  Future<String?> withdraw(int id, double amount, String description) async {
    try {
      await ref
          .read(savingsRepositoryProvider)
          .withdraw(id, amount, description);
      await reload();
      ref.invalidate(dashboardProvider);
      return null;
    } catch (e) {
      return _errorDetail(e) ?? 'Error al registrar el retiro';
    }
  }
}

final savingsListProvider =
    AsyncNotifierProvider<SavingsListNotifier, List<dynamic>>(
      SavingsListNotifier.new,
    );

final savingMovementsProvider = FutureProvider.family<List<dynamic>, int>((
  ref,
  id,
) {
  return ref.read(savingsRepositoryProvider).getMovements(id);
});
