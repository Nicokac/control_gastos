import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/repositories/feedback_repository.dart';

final feedbackRepositoryProvider = Provider<FeedbackRepository>((ref) {
  return FeedbackRepository();
});

class FeedbackNotifier extends StateNotifier<AsyncValue<void>> {
  FeedbackNotifier(this._ref) : super(const AsyncData(null));

  final Ref _ref;

  Future<String?> send({
    required String tipo,
    required String mensaje,
    String? technicalContext,
  }) async {
    state = const AsyncLoading();
    try {
      final repo = _ref.read(feedbackRepositoryProvider);
      await repo.send(
        tipo: tipo,
        mensaje: mensaje,
        technicalContext: technicalContext,
      );
      state = const AsyncData(null);
      return null;
    } on DioException catch (e) {
      state = const AsyncData(null);
      final data = e.response?.data;
      if (data is Map<String, dynamic> && data['detail'] is String) {
        return data['detail'] as String;
      }
      return 'No se pudo enviar el reporte. Intentá de nuevo más tarde.';
    } catch (e) {
      state = const AsyncData(null);
      return 'Error inesperado: $e';
    }
  }
}

final feedbackProvider =
    StateNotifierProvider<FeedbackNotifier, AsyncValue<void>>(
  (ref) => FeedbackNotifier(ref),
);
