import 'package:dio/dio.dart';
import '../../../core/constants/api_constants.dart';
import 'storage_service.dart';

class ApiService {
  static Dio? _dio;

  static Dio get dio {
    _dio ??= _createDio();
    return _dio!;
  }

  static Dio _createDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 60),
        receiveTimeout: const Duration(seconds: 60),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    dio.interceptors.add(_AuthInterceptor(dio));
    return dio;
  }
}

class _AuthInterceptor extends Interceptor {
  final Dio dio;
  _AuthInterceptor(this.dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await StorageService.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        final token = await StorageService.getAccessToken();
        err.requestOptions.headers['Authorization'] = 'Bearer $token';
        final response = await dio.fetch(err.requestOptions);
        return handler.resolve(response);
      }
      await StorageService.clearTokens();
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      final refresh = await StorageService.getRefreshToken();
      if (refresh == null) return false;

      final response = await Dio().post(
        '${ApiConstants.baseUrl}${ApiConstants.tokenRefresh}',
        data: {'refresh': refresh},
      );
      await StorageService.saveTokens(
        access: response.data['access'],
        refresh: refresh,
      );
      return true;
    } catch (_) {
      return false;
    }
  }
}
