import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class NotificationRepository {
  Future<void> registerToken(String token) async {
    await ApiService.dio.post(ApiConstants.deviceToken, data: {'token': token});
  }

  Future<void> unregisterToken(String token) async {
    await ApiService.dio.delete(ApiConstants.deviceToken, data: {'token': token});
  }
}
