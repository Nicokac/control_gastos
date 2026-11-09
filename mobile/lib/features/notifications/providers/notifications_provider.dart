import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/repositories/notification_repository.dart';
import '../../auth/providers/auth_provider.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepository();
});

/// Avisos sin leer, para el punto de la campanita. Se recalcula al cambiar de usuario.
final unreadNotificationsProvider = FutureProvider<int>((ref) async {
  final userId = ref.watch(authProvider.select((auth) => auth.valueOrNull?['id']));
  if (userId == null) return 0;
  return ref.read(notificationRepositoryProvider).getUnreadCount();
});

/// Historial de avisos. Se descarta al salir de la pantalla para traerlo fresco en cada visita.
class NotificationListNotifier extends AutoDisposeAsyncNotifier<List<dynamic>> {
  @override
  Future<List<dynamic>> build() async {
    final repo = ref.read(notificationRepositoryProvider);
    final items = await repo.getNotifications();
    // Se marcan como leídos después de traerlos: en esta visita siguen mostrando el punto.
    if (items.any((n) => n['read_at'] == null)) {
      try {
        await repo.markAllRead();
        ref.invalidate(unreadNotificationsProvider);
      } catch (e) {
        debugPrint('Notificaciones: no se pudieron marcar como leídas: $e');
      }
    }
    return items;
  }

  Future<void> reload() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(build);
  }
}

final notificationListProvider =
    AsyncNotifierProvider.autoDispose<NotificationListNotifier, List<dynamic>>(
  NotificationListNotifier.new,
);
