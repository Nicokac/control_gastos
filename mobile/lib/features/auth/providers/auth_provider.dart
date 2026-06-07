import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

final isLoggedInProvider = FutureProvider<bool>((ref) async {
  final repo = ref.read(authRepositoryProvider);
  return repo.isLoggedIn();
});

class AuthNotifier extends AsyncNotifier<Map<String, dynamic>?> {
  @override
  Future<Map<String, dynamic>?> build() async {
    final repo = ref.read(authRepositoryProvider);
    final loggedIn = await repo.isLoggedIn();
    if (!loggedIn) return null;
    return repo.getProfile();
  }

  Future<String?> login({required String email, required String password}) async {
    state = const AsyncLoading();
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.login(email: email, password: password);
      final profile = await repo.getProfile();
      state = AsyncData(profile);
      return null;
    } catch (e) {
      state = const AsyncData(null);
      if (e is DioException) {
        final status = e.response?.statusCode;
        if (status == 400 || status == 401) {
          return 'Email o contraseña incorrectos';
        }
        if (e.type == DioExceptionType.connectionTimeout ||
            e.type == DioExceptionType.receiveTimeout ||
            e.type == DioExceptionType.connectionError) {
          return 'No se pudo conectar al servidor. Intentá de nuevo en unos segundos.';
        }
      }
      return 'Error inesperado: $e';
    }
  }

  Future<bool> updateProfile(Map<String, dynamic> data) async {
    try {
      final repo = ref.read(authRepositoryProvider);
      final updated = await repo.updateProfile(data);
      state = AsyncData(updated);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    final repo = ref.read(authRepositoryProvider);
    await repo.logout();
    state = const AsyncData(null);
  }
}

final authProvider =
    AsyncNotifierProvider<AuthNotifier, Map<String, dynamic>?>(
  AuthNotifier.new,
);
