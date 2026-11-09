import 'package:flutter/material.dart';

/// Acceso directo del dashboard. En pantallas muy angostas o con la fuente del
/// sistema muy agrandada, el texto se achica en vez de partirse en dos líneas (DT-103).
class DashboardShortcutButton extends StatelessWidget {
  const DashboardShortcutButton({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onPressed,
    this.borderColor,
  });

  final IconData icon;
  final String label;
  final Color color;
  final Color? borderColor;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    // Ícono arriba y texto abajo: con el ícono al costado, en 360 dp quedaban ~64 dp
    // para el texto y "Compartidos" se partía en dos líneas.
    return OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        foregroundColor: color,
        side: BorderSide(color: borderColor ?? color),
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 20),
          const SizedBox(height: 4),
          FittedBox(fit: BoxFit.scaleDown, child: Text(label, maxLines: 1)),
        ],
      ),
    );
  }
}
