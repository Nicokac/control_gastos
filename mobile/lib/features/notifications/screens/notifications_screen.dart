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
          const _RemindersToggle(),
          const Divider(height: 1),
          Expanded(
            child: notificationsAsync.when(
              loading: () => const ListSkeleton(),
              error: (e, _) => ErrorStateView(error: e, onRetry: notifier.reload),
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
                                'Te avisamos acá 3 días antes de que venza un gasto fijo',
                          ),
                        ],
                      )
                    : ListView.separated(
                        itemCount: items.length,
                        separatorBuilder: (_, _) => const Divider(height: 1),
                        itemBuilder: (_, i) =>
                            _NotificationTile(notification: items[i] as Map<String, dynamic>),
                      ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RemindersToggle extends ConsumerStatefulWidget {
  const _RemindersToggle();

  @override
  ConsumerState<_RemindersToggle> createState() => _RemindersToggleState();
}

class _RemindersToggleState extends ConsumerState<_RemindersToggle> {
  bool _saving = false;

  Future<void> _toggle(bool enabled) async {
    setState(() => _saving = true);
    final ok = await ref
        .read(authProvider.notifier)
        .updateProfile({'recurring_reminders_enabled': enabled});
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
    final enabled = user?['recurring_reminders_enabled'] as bool? ?? true;

    return SwitchListTile(
      title: const Text('Recordatorios de gastos fijos'),
      subtitle: const Text('Aviso 3 días antes de cada vencimiento'),
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

    return ListTile(
      leading: Badge(
        isLabelVisible: unread,
        backgroundColor: colorScheme.primary,
        child: Icon(Icons.event_repeat, color: context.semanticColors.recurring),
      ),
      title: Text(
        notification['title'] as String? ?? '',
        style: TextStyle(fontWeight: unread ? FontWeight.bold : FontWeight.normal),
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
