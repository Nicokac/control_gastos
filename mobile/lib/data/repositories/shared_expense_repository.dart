import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

class SharedExpenseRepository {
  Future<List<dynamic>> getSharedExpenses({int? month, int? year}) async {
    final params = <String, dynamic>{'page_size': 200};
    if (month != null) params['month'] = month;
    if (year != null) params['year'] = year;

    final response = await ApiService.dio.get(
      ApiConstants.sharedExpenses,
      queryParameters: params,
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createSharedExpense(
      Map<String, dynamic> data) async {
    final response =
        await ApiService.dio.post(ApiConstants.sharedExpenses, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateSharedExpense(
      int id, Map<String, dynamic> data) async {
    final response = await ApiService.dio
        .put('${ApiConstants.sharedExpenses}$id/', data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteSharedExpense(int id) async {
    await ApiService.dio.delete('${ApiConstants.sharedExpenses}$id/');
  }

  Future<List<dynamic>> getMembers() async {
    final response = await ApiService.dio.get(
      ApiConstants.householdMembers,
      queryParameters: {'page_size': 200},
    );
    return _extractList(response.data);
  }

  Future<Map<String, dynamic>> createMember(String name) async {
    final response = await ApiService.dio
        .post(ApiConstants.householdMembers, data: {'name': name});
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteMember(int id) async {
    await ApiService.dio.delete('${ApiConstants.householdMembers}$id/');
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
