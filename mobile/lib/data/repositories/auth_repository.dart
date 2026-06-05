import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../../core/constants/api_constants.dart';

class AuthRepository {
  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await ApiService.dio.post(
      ApiConstants.tokenObtain,
      data: {'username': email, 'password': password},
    );
    await StorageService.saveTokens(
      access: response.data['access'],
      refresh: response.data['refresh'],
    );
  }

  Future<void> register({
    required String email,
    required String username,
    required String password,
    required String password2,
  }) async {
    await ApiService.dio.post(
      ApiConstants.register,
      data: {
        'email': email,
        'username': username,
        'password': password,
        'password2': password2,
      },
    );
  }

  Future<Map<String, dynamic>> getProfile() async {
    final response = await ApiService.dio.get(ApiConstants.me);
    return response.data as Map<String, dynamic>;
  }

  Future<void> logout() async {
    await StorageService.clearTokens();
  }

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final response = await ApiService.dio.put(ApiConstants.me, data: data);
    return response.data as Map<String, dynamic>;
  }

  Future<bool> isLoggedIn() => StorageService.hasTokens();
}
