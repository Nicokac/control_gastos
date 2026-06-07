import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../../core/constants/api_constants.dart';

class ExpenseRepository {
  Future<List<dynamic>> getExpenses({int? month, int? year, int? category}) async {
    final cacheKey = 'expenses_${month}_${year}_$category';
    final params = <String, dynamic>{'page_size': 200};
    if (month != null) params['month'] = month;
    if (year != null) params['year'] = year;
    if (category != null) params['category'] = category;

    try {
      final response = await ApiService.dio.get(
        ApiConstants.expenses,
        queryParameters: params,
      );
      final data = _extractList(response.data);
      await CacheService.save(cacheKey, data);
      return data;
    } catch (_) {
      final cached = await CacheService.load(cacheKey);
      if (cached != null) return cached as List<dynamic>;
      rethrow;
    }
  }

  Future<Map<String, dynamic>> createExpense(Map<String, dynamic> data) async {
    final response = await ApiService.dio.post(ApiConstants.expenses, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateExpense(
      int id, Map<String, dynamic> data) async {
    final response =
        await ApiService.dio.put('${ApiConstants.expenses}$id/', data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteExpense(int id) async {
    await ApiService.dio.delete('${ApiConstants.expenses}$id/');
  }

  Future<List<dynamic>> getCategories() async {
    final response = await ApiService.dio.get(
      ApiConstants.categories,
      queryParameters: {'page_size': 200},
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createCategory(Map<String, dynamic> data) async {
    final response = await ApiService.dio.post(ApiConstants.categories, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteCategory(int id) async {
    await ApiService.dio.delete('${ApiConstants.categories}$id/');
  }

  List<dynamic> _extractList(dynamic data) {
    if (data is List) return data;
    if (data is Map && data.containsKey('results')) {
      return data['results'] as List<dynamic>;
    }
    return [];
  }
}
