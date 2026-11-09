import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'routing/app_router.dart';
import 'core/providers/theme_provider.dart';
import 'core/theme/app_radius.dart';
import 'core/theme/app_semantic_colors.dart';
import 'data/services/push_notification_service.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/notifications/providers/notifications_provider.dart';

class App extends ConsumerStatefulWidget {
  const App({super.key});

  @override
  ConsumerState<App> createState() => _AppState();
}

class _AppState extends ConsumerState<App> {
  final _messengerKey = GlobalKey<ScaffoldMessengerState>();
  final _pushSubscriptions = <StreamSubscription<RemoteMessage>>[];

  @override
  void initState() {
    super.initState();
    _pushSubscriptions
      ..add(FirebaseMessaging.onMessage.listen(_showInAppNotice))
      ..add(FirebaseMessaging.onMessageOpenedApp.listen(_openFromPush));
    FirebaseMessaging.instance.getInitialMessage().then((message) {
      if (message != null) _openFromPush(message, coldStart: true);
    });
  }

  @override
  void dispose() {
    for (final subscription in _pushSubscriptions) {
      subscription.cancel();
    }
    super.dispose();
  }

  /// Push tocado con la app en segundo plano o cerrada (D-019).
  Future<void> _openFromPush(RemoteMessage message, {bool coldStart = false}) async {
    ref.invalidate(unreadNotificationsProvider);
    final route = routeForPushData(message.data);
    if (route == null) return;
    final profile = await ref.read(authProvider.future);
    if (profile == null || !mounted) return;
    final router = ref.read(routerProvider);
    // En arranque en frío el stack es /splash: se arma dashboard debajo para que "atrás" funcione.
    if (coldStart) router.go('/dashboard');
    router.push(route);
  }

  /// Con la app abierta Android no muestra la notificación del sistema: se avisa dentro de la app.
  void _showInAppNotice(RemoteMessage message) {
    ref.invalidate(unreadNotificationsProvider);
    final notification = message.notification;
    if (notification == null) return;
    final route = routeForPushData(message.data);
    _messengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Text(notification.body ?? notification.title ?? ''),
        duration: const Duration(seconds: 6),
        action: route == null
            ? null
            : SnackBarAction(
                label: 'Ver',
                onPressed: () => ref.read(routerProvider).push(route),
              ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.read(routerProvider);
    final themeMode = ref.watch(themeProvider);

    return MaterialApp.router(
      title: 'Control de Gastos',
      debugShowCheckedModeBanner: false,
      scaffoldMessengerKey: _messengerKey,
      themeMode: themeMode,
      theme: _lightTheme,
      darkTheme: _darkTheme,
      routerConfig: router,
    );
  }
}

final _lightTheme = ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: const Color(0xFF0d6efd),
    brightness: Brightness.light,
  ),
  useMaterial3: true,
  appBarTheme: const AppBarTheme(
    centerTitle: false,
    elevation: 0,
    scrolledUnderElevation: 1,
  ),
  cardTheme: CardThemeData(
    elevation: 2,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.card)),
  ),
  inputDecorationTheme: InputDecorationTheme(
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadius.card),
    ),
  ),
  extensions: const [AppSemanticColors.light],
);

final _darkTheme = ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: const Color(0xFF0d6efd),
    brightness: Brightness.dark,
  ),
  useMaterial3: true,
  appBarTheme: const AppBarTheme(
    centerTitle: false,
    elevation: 0,
    scrolledUnderElevation: 1,
  ),
  cardTheme: CardThemeData(
    elevation: 2,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.card)),
  ),
  inputDecorationTheme: InputDecorationTheme(
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadius.card),
    ),
  ),
  extensions: const [AppSemanticColors.dark],
);
