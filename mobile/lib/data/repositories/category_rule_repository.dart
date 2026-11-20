import 'package:dio/dio.dart';

import '../services/api_service.dart';
import '../../core/constants/api_constants.dart';

/// El backend rechazó la regla; [fieldErrors] trae el mensaje de cada campo
/// ('pattern' o 'category') para mostrarlo debajo del que corresponde.
class CategoryRuleException implements Exception {
  final Map<String, String> fieldErrors;
  const CategoryRuleException(this.fieldErrors);

  @override
  String toString() => fieldErrors.values.join('\n');
}

class CategoryRuleRepository {
  Future<List<dynamic>> getRules() async {
    final response = await ApiService.dio.get(
      ApiConstants.categoryRules,
      queryParameters: {'page_size': 200},
    );
    final data = response.data;
    if (data is Map && data['results'] is List) return data['results'] as List;
    return data is List ? data : [];
  }

  Future<void> saveRule({int? id, required String pattern, required int category}) async {
    final data = {'pattern': pattern, 'category': category};
    try {
      if (id == null) {
        await ApiService.dio.post(ApiConstants.categoryRules, data: data);
      } else {
        await ApiService.dio.put('${ApiConstants.categoryRules}$id/', data: data);
      }
    } on DioException catch (e) {
      final body = e.response?.data;
      if (e.response?.statusCode == 400 && body is Map) {
        throw CategoryRuleException({
          for (final entry in body.entries)
            if (entry.value is List && (entry.value as List).isNotEmpty)
              entry.key as String: (entry.value as List).first.toString(),
        });
      }
      rethrow;
    }
  }

  Future<void> deleteRule(int id) async {
    await ApiService.dio.delete('${ApiConstants.categoryRules}$id/');
  }
}
