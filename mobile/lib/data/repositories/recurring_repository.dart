import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class RecurringRepository {
  Future<List<dynamic>> getRecurring() async {
    final response = await ApiService.dio.get(
      ApiConstants.recurring,
      queryParameters: {'page_size': 200},
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createRecurring(Map<String, dynamic> data) async {
    final response = await ApiService.dio.post(ApiConstants.recurring, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateRecurring(int id, Map<String, dynamic> data) async {
    final response =
        await ApiService.dio.put('${ApiConstants.recurring}$id/', data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteRecurring(int id) async {
    await ApiService.dio.delete('${ApiConstants.recurring}$id/');
  }

  Future<Map<String, dynamic>> markPaid(int id, {double? amount}) async {
    final data = <String, dynamic>{};
    if (amount != null) data['amount'] = amount;
    final response = await ApiService.dio.post(
      '${ApiConstants.recurring}$id/mark-paid/',
      data: data,
    );
    return response.data as Map<String, dynamic>;
  }

  Future<void> unmarkPaid(int id) async {
    await ApiService.dio.post('${ApiConstants.recurring}$id/unmark-paid/');
  }

  Future<List<dynamic>> getCategories() async {
    final response = await ApiService.dio.get(
      ApiConstants.categories,
      queryParameters: {'page_size': 200, 'type': 'EXPENSE'},
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
