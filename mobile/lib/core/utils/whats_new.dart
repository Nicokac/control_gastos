import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/api_constants.dart';

const _kWhatsNewSeenKey = 'whats_new_seen_version';

/// Muestra un diálogo con las novedades de la versión actual si el usuario
/// todavía no lo vio en este dispositivo (DT-068). Se llama una vez al
/// entrar al dashboard.
Future<void> maybeShowWhatsNewDialog(BuildContext context) async {
  final prefs = await SharedPreferences.getInstance();
  final seen = prefs.getString(_kWhatsNewSeenKey);
  final current = (await PackageInfo.fromPlatform()).version;

  if (seen == current) return;
  if (!context.mounted) return;

  await showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      icon: const Icon(Icons.auto_awesome, color: Colors.amber),
      title: Text('Novedades v$current'),
      content: Text(ApiConstants.latestReleaseSummary),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(),
          child: const Text('Entendido'),
        ),
      ],
    ),
  );

  await prefs.setString(_kWhatsNewSeenKey, current);
}
