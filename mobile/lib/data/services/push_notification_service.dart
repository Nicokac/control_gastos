import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../repositories/notification_repository.dart';

const _kRegisteredFidKey = 'push_registered_fid';

/// Pantalla a abrir según el `type` que manda el backend en el push.
String? routeForPushData(Map<String, dynamic> data) {
  return switch (data['type']) {
    'recurring_reminder' || 'recurring_overdue' => '/recurring',
    'spending_threshold' => '/expenses',
    'category_threshold' => '/categories',
    _ => null,
  };
}

/// Registra el dispositivo en Firebase y le informa al backend su
/// Firebase Installation ID (FID) para recibir push (D-019).
///
/// El FID se guarda localmente porque Android no garantiza volver a emitir
/// `onRegistered` en cada arranque, y en el logout hace falta saber cuál
/// desactivar en el backend.
class PushNotificationService {
  final FirebaseMessaging _messaging;
  final NotificationRepository _repository;
  StreamSubscription<String>? _registeredSubscription;

  PushNotificationService(this._messaging, this._repository);

  Future<void> registerDevice() async {
    final settings = await _messaging.requestPermission();
    if (settings.authorizationStatus == AuthorizationStatus.denied) return;

    _registeredSubscription ??= _messaging.onRegistered.listen(_onRegistered);

    final prefs = await SharedPreferences.getInstance();
    final storedFid = prefs.getString(_kRegisteredFidKey);
    if (storedFid != null) {
      await _repository.registerToken(storedFid);
    }

    await _messaging.register();
  }

  Future<void> unregisterDevice() async {
    await _registeredSubscription?.cancel();
    _registeredSubscription = null;

    final prefs = await SharedPreferences.getInstance();
    final storedFid = prefs.getString(_kRegisteredFidKey);
    if (storedFid != null) {
      await _repository.unregisterToken(storedFid);
      await prefs.remove(_kRegisteredFidKey);
    }

    await _messaging.unregister();
  }

  Future<void> _onRegistered(String fid) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kRegisteredFidKey, fid);
    try {
      await _repository.registerToken(fid);
    } catch (e) {
      // Sin red: el FID ya quedó guardado y se reenvía en el próximo arranque.
      debugPrint('Push: no se pudo informar el FID al backend: $e');
    }
  }
}
