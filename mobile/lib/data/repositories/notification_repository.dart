import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class NotificationRepository {
  Future<void> registerToken(String token) async {
    await ApiService.dio.post(ApiConstants.deviceToken, data: {'token': token});
  }

  Future<void> unregisterToken(String token) async {
    await ApiService.dio.delete(ApiConstants.deviceToken, data: {'token': token});
  }

  Future<List<dynamic>> getNotifications() async {
    final response = await ApiService.dio.get(ApiConstants.notifications);
    final data = response.data;
    if (data is Map && data['results'] is List) return data['results'] as List<dynamic>;
    return [];
  }

  Future<int> getUnreadCount() async {
    final response = await ApiService.dio.get(ApiConstants.notificationsUnreadCount);
    return (response.data as Map<String, dynamic>)['unread'] as int;
  }

  Future<void> markAllRead() async {
    await ApiService.dio.post(ApiConstants.notificationsMarkRead);
  }
}
