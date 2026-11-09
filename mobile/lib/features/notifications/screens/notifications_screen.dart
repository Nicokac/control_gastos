import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_semantic_colors.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state_view.dart';
import '../../../core/widgets/list_skeleton.dart';
import '../../../data/services/push_notification_service.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/notifications_provider.dart';

/// "Hoy 09:00", "Ayer 09:00" o "07/11/2026", en hora local.
String formatNotificationDate(DateTime created, DateTime now) {
  final local = created.toLocal();
  final today = DateTime(now.year, now.month, now.day);
  final day = DateTime(local.year, local.month, local.day);
  final time = DateFormat('HH:mm').format(local);
  final daysAgo = today.difference(day).inDays;
  if (daysAgo == 0) return 'Hoy $time';
  if (daysAgo == 1) return 'Ayer $time';
  return DateFormat('dd/MM/yyyy').format(local);
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsAsync = ref.watch(notificationListProvider);
    final notifier = ref.read(notificationListProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('Notificaciones')),
      body: Column(
        children: [
          const _PreferenceToggle(
            field: 'recurring_reminders_enabled',
            title: 'Recordatorios de gastos fijos',
            subtitle: 'Antes de cada vencimiento y si quedó sin pagar',
          ),
          const _PreferenceToggle(
            field: 'spending_alerts_enabled',
            title: 'Alertas de gastos',
            subtitle:
                'Al superar el umbral del período o el límite de una subcategoría',
          ),
          const Divider(height: 1),
          Expanded(
            child: notificationsAsync.when(
              loading: () => const ListSkeleton(),
              error: (e, _) =>
                  ErrorStateView(error: e, onRetry: notifier.reload),
              data: (items) => RefreshIndicator(
                onRefresh: notifier.reload,
                child: items.isEmpty
                    ? ListView(
                        children: const [
                          SizedBox(height: 48),
                          EmptyState(
                            icon: Icons.notifications_none,
                            title: 'Sin notificaciones',
                            subtitle:
                                'Acá vas a ver los recordatorios de gastos fijos y las alertas de gastos',
                          ),
                        ],
                      )
                    : ListView.separated(
                        itemCount: items.length,
                        separatorBuilder: (_, _) => const Divider(height: 1),
                        itemBuilder: (_, i) => _NotificationTile(
                          notification: items[i] as Map<String, dynamic>,
                        ),
                      ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Ícono del historial según el tipo de aviso (D-019).
IconData iconForNotificationType(String? type) {
  return switch (type) {
    'recurring_overdue' => Icons.event_busy,
    'spending_threshold' || 'category_threshold' => Icons.trending_up,
    _ => Icons.event_repeat,
  };
}

/// Interruptor de una preferencia booleana del perfil (`/auth/me/`).
class _PreferenceToggle extends ConsumerStatefulWidget {
  const _PreferenceToggle({
    required this.field,
    required this.title,
    required this.subtitle,
  });

  final String field;
  final String title;
  final String subtitle;

  @override
  ConsumerState<_PreferenceToggle> createState() => _PreferenceToggleState();
}

class _PreferenceToggleState extends ConsumerState<_PreferenceToggle> {
  bool _saving = false;

  Future<void> _toggle(bool enabled) async {
    setState(() => _saving = true);
    final ok = await ref.read(authProvider.notifier).updateProfile({
      widget.field: enabled,
    });
    if (!mounted) return;
    setState(() => _saving = false);
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('No se pudo guardar la preferencia'),
          backgroundColor: context.semanticColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).valueOrNull;
    final enabled = user?[widget.field] as bool? ?? true;

    return SwitchListTile(
      title: Text(widget.title),
      subtitle: Text(widget.subtitle),
      value: enabled,
      onChanged: _saving ? null : _toggle,
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final Map<String, dynamic> notification;

  const _NotificationTile({required this.notification});

  @override
  Widget build(BuildContext context) {
    final unread = notification['read_at'] == null;
    final route = routeForPushData({'type': notification['type']});
    final created = DateTime.parse(notification['created_at'] as String);
    final colorScheme = Theme.of(context).colorScheme;
    final colors = context.semanticColors;
    final type = notification['type'] as String?;
    final iconColor = switch (type) {
      'recurring_overdue' => colors.overdue,
      'spending_threshold' || 'category_threshold' => colors.expense,
      _ => colors.recurring,
    };

    return ListTile(
      leading: Badge(
        isLabelVisible: unread,
        backgroundColor: colorScheme.primary,
        child: Icon(iconForNotificationType(type), color: iconColor),
      ),
      title: Text(
        notification['title'] as String? ?? '',
        style: TextStyle(
          fontWeight: unread ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      subtitle: Text(notification['body'] as String? ?? ''),
      trailing: Text(
        formatNotificationDate(created, DateTime.now()),
        style: Theme.of(context).textTheme.bodySmall,
      ),
      isThreeLine: true,
      onTap: route == null ? null : () => context.push(route),
    );
  }
}
