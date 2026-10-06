import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';

String _firstErrorMessage(DioException e, String fallback) {
  final data = e.response?.data;
  if (data is Map<String, dynamic>) {
    for (final value in data.values) {
      if (value is List && value.isNotEmpty) return value.first.toString();
      if (value is String) return value;
    }
  }
  return fallback;
}

class PasswordResetNotifier extends StateNotifier<AsyncValue<void>> {
  PasswordResetNotifier(this._ref) : super(const AsyncData(null));

  final Ref _ref;

  Future<String?> requestReset(String email) async {
    state = const AsyncLoading();
    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.requestPasswordReset(email);
      state = const AsyncData(null);
      return null;
    } on DioException catch (e) {
      state = const AsyncData(null);
      return _firstErrorMessage(e, 'No se pudo enviar el email. Intentá de nuevo.');
    } catch (e) {
      state = const AsyncData(null);
      return 'Error inesperado: $e';
    }
  }

  Future<String?> confirmReset({
    required String uid,
    required String token,
    required String newPassword,
    required String newPassword2,
  }) async {
    state = const AsyncLoading();
    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.confirmPasswordReset(
        uid: uid,
        token: token,
        newPassword: newPassword,
        newPassword2: newPassword2,
      );
      state = const AsyncData(null);
      return null;
    } on DioException catch (e) {
      state = const AsyncData(null);
      return _firstErrorMessage(
        e,
        'No se pudo cambiar la contraseña. Verificá el código e intentá de nuevo.',
      );
    } catch (e) {
      state = const AsyncData(null);
      return 'Error inesperado: $e';
    }
  }
}

final passwordResetProvider =
    StateNotifierProvider<PasswordResetNotifier, AsyncValue<void>>(
  (ref) => PasswordResetNotifier(ref),
);
