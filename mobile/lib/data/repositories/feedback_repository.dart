import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class FeedbackRepository {
  Future<void> send({
    required String tipo,
    required String mensaje,
    String? technicalContext,
  }) async {
    await ApiService.dio.post(
      ApiConstants.feedback,
      data: {
        'tipo': tipo,
        'mensaje': mensaje,
        if (technicalContext != null && technicalContext.isNotEmpty)
          'technical_context': technicalContext,
      },
    );
  }
}
