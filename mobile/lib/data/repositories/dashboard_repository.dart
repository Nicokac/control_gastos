import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class DashboardRepository {
  Future<Map<String, dynamic>> getDashboard({
    required int month,
    required int year,
  }) async {
    final response = await ApiService.dio.get(
      ApiConstants.dashboard,
      queryParameters: {'month': month, 'year': year},
    );
    return response.data as Map<String, dynamic>;
  }
}
