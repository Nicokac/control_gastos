import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class SavingsRepository {
  Future<List<dynamic>> getSavings() async {
    final response = await ApiService.dio.get(
      ApiConstants.savings,
      queryParameters: {'page_size': 200},
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createSaving(Map<String, dynamic> data) async {
    final response = await ApiService.dio.post(ApiConstants.savings, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateSaving(int id, Map<String, dynamic> data) async {
    final response =
        await ApiService.dio.put('${ApiConstants.savings}$id/', data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteSaving(int id) async {
    await ApiService.dio.delete('${ApiConstants.savings}$id/');
  }

  Future<Map<String, dynamic>> deposit(int id, double amount, String description) async {
    final response = await ApiService.dio.post(
      '${ApiConstants.savings}$id/deposit/',
      data: {'amount': amount, 'description': description},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> withdraw(int id, double amount, String description) async {
    final response = await ApiService.dio.post(
      '${ApiConstants.savings}$id/withdraw/',
      data: {'amount': amount, 'description': description},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> getMovements(int id) async {
    final response = await ApiService.dio.get('${ApiConstants.savings}$id/movements/');
    return response.data as List<dynamic>;
  }

  List<dynamic> _extractList(dynamic data) {
    if (data is List) return data;
    if (data is Map && data.containsKey('results')) {
      return data['results'] as List<dynamic>;
    }
    return [];
  }
}
