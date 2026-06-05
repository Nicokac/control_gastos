import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class IncomeRepository {
  Future<List<dynamic>> getIncome({int? month, int? year}) async {
    final params = <String, dynamic>{'page_size': 200};
    if (month != null) params['month'] = month;
    if (year != null) params['year'] = year;

    final response = await ApiService.dio.get(
      ApiConstants.income,
      queryParameters: params,
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createIncome(Map<String, dynamic> data) async {
    final response = await ApiService.dio.post(ApiConstants.income, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateIncome(int id, Map<String, dynamic> data) async {
    final response =
        await ApiService.dio.put('${ApiConstants.income}$id/', data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteIncome(int id) async {
    await ApiService.dio.delete('${ApiConstants.income}$id/');
  }

  Future<List<dynamic>> getCategories() async {
    final response = await ApiService.dio.get(
      ApiConstants.categories,
      queryParameters: {'page_size': 200},
    );
    return _extractList(response.data);
  }

  List<dynamic> _extractList(dynamic data) {
    if (data is List) return data;
    if (data is Map && data.containsKey('results')) {
      return data['results'] as List<dynamic>;
    }
    return [];
  }
}
