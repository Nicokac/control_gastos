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
      final msg = e.toString();
      if (msg.contains('400') || msg.contains('401')) {
        return 'Email o contraseña incorrectos';
      } else if (msg.contains('SocketException') ||
          msg.contains('connection') ||
          msg.contains('timeout') ||
          msg.contains('timed out')) {
        return 'No se pudo conectar al servidor. Intentá de nuevo en unos segundos.';
      }
      return 'Error inesperado: $msg';
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
