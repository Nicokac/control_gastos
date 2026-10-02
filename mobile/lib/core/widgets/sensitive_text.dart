import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/amounts_visibility_provider.dart';

/// Igual que Text, pero enmascara el valor si el usuario ocultó los
/// montos desde el botón de ojo del dashboard (ver DT-065).
class SensitiveText extends ConsumerWidget {
  final String text;
  final TextStyle? style;
  final TextOverflow? overflow;
  final TextAlign? textAlign;

  const SensitiveText(
    this.text, {
    super.key,
    this.style,
    this.overflow,
    this.textAlign,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hidden = ref.watch(amountsHiddenProvider);
    return Text(
      hidden ? '••••••' : text,
      style: style,
      overflow: overflow,
      textAlign: textAlign,
    );
  }
}
