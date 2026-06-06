import 'dart:async';
import 'package:flutter/material.dart';

class LastUpdatedLabel extends StatefulWidget {
  final DateTime? lastUpdated;

  const LastUpdatedLabel({super.key, required this.lastUpdated});

  @override
  State<LastUpdatedLabel> createState() => _LastUpdatedLabelState();
}

class _LastUpdatedLabelState extends State<LastUpdatedLabel> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String _relativeLabel(DateTime updated) {
    final diff = DateTime.now().difference(updated);
    if (diff.inSeconds < 30) return 'Actualizado ahora';
    if (diff.inMinutes < 1) return 'Actualizado hace segundos';
    if (diff.inMinutes == 1) return 'Actualizado hace 1 minuto';
    if (diff.inMinutes < 60) return 'Actualizado hace ${diff.inMinutes} minutos';
    if (diff.inHours == 1) return 'Actualizado hace 1 hora';
    if (diff.inHours < 24) return 'Actualizado hace ${diff.inHours} horas';
    return 'Actualizado hace ${diff.inDays} días';
  }

  @override
  Widget build(BuildContext context) {
    final updated = widget.lastUpdated;
    if (updated == null) return const SizedBox.shrink();

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.cloud_done_outlined, size: 13, color: Colors.grey[500]),
        const SizedBox(width: 4),
        Text(
          _relativeLabel(updated),
          style: TextStyle(fontSize: 12, color: Colors.grey[500]),
        ),
      ],
    );
  }
}
