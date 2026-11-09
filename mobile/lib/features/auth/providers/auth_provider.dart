import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/providers/push_notification_provider.dart';
import '../../../data/repositories/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

final isLoggedInProvider = FutureProvider<bool>((ref) async {
  final repo = ref.read(authRepositoryProvider);
  return repo.isLoggedIn();
});

class AuthNotifier extends AsyncNotifier<Map<String, dynamic>?> {
  static const int _failureLimit = 5;
  int _failureCount = 0;

  @override
  Future<Map<String, dynamic>?> build() async {
    final repo = ref.read(authRepositoryProvider);
    final loggedIn = await repo.isLoggedIn();
    if (!loggedIn) return null;
    final profile = await repo.getProfile();
    unawaited(_registerPushDevice());
    return profile;
  }

  /// El push nunca debe bloquear ni romper el login: sin permiso, sin red o
  /// sin Firebase, la app sigue funcionando igual.
  Future<void> _registerPushDevice() async {
    try {
      await ref.read(pushNotificationServiceProvider).registerDevice();
    } catch (e) {
      debugPrint('Push: no se pudo registrar el dispositivo: $e');
    }
  }

  Future<String?> login({required String email, required String password}) async {
    state = const AsyncLoading();
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.login(email: email, password: password);
      _failureCount = 0;
      final profile = await repo.getProfile();
      state = AsyncData(profile);
      unawaited(_registerPushDevice());
      return null;
    } catch (e) {
      state = const AsyncData(null);
      if (e is DioException) {
        final status = e.response?.statusCode;
        if (status == 429) {
          _failureCount = _failureLimit;
          return 'Tu cuenta fue bloqueada temporalmente por demasiados intentos fallidos. Intentá de nuevo en 1 hora.';
        }
        if (status == 400 || status == 401) {
          _failureCount++;
          final remaining = _failureLimit - _failureCount;
          if (_failureCount >= 2 && remaining > 0) {
            return 'Email o contraseña incorrectos. Te quedan $remaining intento${remaining != 1 ? 's' : ''} antes de que se bloquee tu cuenta.';
          }
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
    // Antes de borrar el JWT: el backend necesita saber quién desactiva el dispositivo.
    try {
      await ref
          .read(pushNotificationServiceProvider)
          .unregisterDevice()
          .timeout(const Duration(seconds: 5));
    } catch (e) {
      debugPrint('Push: no se pudo desregistrar el dispositivo: $e');
    }
    final repo = ref.read(authRepositoryProvider);
    await repo.logout();
    state = const AsyncData(null);
  }
}

final authProvider =
    AsyncNotifierProvider<AuthNotifier, Map<String, dynamic>?>(
  AuthNotifier.new,
);
