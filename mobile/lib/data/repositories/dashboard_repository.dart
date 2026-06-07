import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../../core/constants/api_constants.dart';

class DashboardRepository {
  Future<Map<String, dynamic>> getDashboard({
    required int month,
    required int year,
  }) async {
    final cacheKey = 'dashboard_${month}_$year';
    try {
      final response = await ApiService.dio.get(
        ApiConstants.dashboard,
        queryParameters: {'month': month, 'year': year},
      );
      final data = response.data as Map<String, dynamic>;
      await CacheService.save(cacheKey, data);
      return data;
    } catch (_) {
      final cached = await CacheService.load(cacheKey);
      if (cached != null) return cached as Map<String, dynamic>;
      rethrow;
    }
  }
}
