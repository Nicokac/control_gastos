import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/providers/auth_provider.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _usernameCtrl = TextEditingController();

  String _defaultCurrency = 'ARS';
  int _monthStartDay = 1;
  bool _loading = false;
  bool _initialized = false;

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _usernameCtrl.dispose();
    super.dispose();
  }

  void _initFromUser(Map<String, dynamic> user) {
    if (_initialized) return;
    _initialized = true;
    _firstNameCtrl.text = user['first_name'] as String? ?? '';
    _lastNameCtrl.text = user['last_name'] as String? ?? '';
    _usernameCtrl.text = user['username'] as String? ?? '';
    _defaultCurrency = user['default_currency'] as String? ?? 'ARS';
    _monthStartDay = (user['financial_month_start_day'] as int?) ?? 1;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final ok = await ref.read(authProvider.notifier).updateProfile({
      'first_name': _firstNameCtrl.text.trim(),
      'last_name': _lastNameCtrl.text.trim(),
      'username': _usernameCtrl.text.trim(),
      'default_currency': _defaultCurrency,
      'financial_month_start_day': _monthStartDay,
    });

    setState(() => _loading = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ok ? 'Perfil actualizado' : 'Error al guardar'),
          backgroundColor: ok ? Colors.green[700] : Colors.red[700],
        ),
      );
    }
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Querés cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(authProvider.notifier).logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    final userAsync = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuración'),
        actions: [
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                  child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))),
            )
          else
            TextButton(
              onPressed: _submit,
              child: const Text('Guardar',
                  style: TextStyle(fontWeight: FontWeight.bold)),
            ),
        ],
      ),
      body: userAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (user) {
          if (user == null) return const SizedBox.shrink();
          _initFromUser(user);

          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Email (solo lectura)
                _SectionLabel('Cuenta'),
                const SizedBox(height: 8),
                InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                    suffixIcon: Icon(Icons.lock_outline, size: 16),
                  ),
                  child: Text(
                    user['email'] as String? ?? '',
                    style: const TextStyle(color: Colors.grey),
                  ),
                ),
                const SizedBox(height: 16),

                // Nombre
                TextFormField(
                  controller: _firstNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),

                // Apellido
                TextFormField(
                  controller: _lastNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Apellido',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),

                // Username
                TextFormField(
                  controller: _usernameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre de usuario',
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty)
                          ? 'El usuario no puede estar vacío'
                          : null,
                ),
                const SizedBox(height: 24),

                _SectionLabel('Preferencias'),
                const SizedBox(height: 8),

                // Moneda por defecto
                DropdownButtonFormField<String>(
                  value: _defaultCurrency,
                  decoration: const InputDecoration(
                    labelText: 'Moneda por defecto',
                    border: OutlineInputBorder(),
                  ),
                  items: const [
                    DropdownMenuItem(
                        value: 'ARS', child: Text('Peso Argentino')),
                    DropdownMenuItem(
                        value: 'USD', child: Text('Dólar Estadounidense')),
                  ],
                  onChanged: (v) =>
                      setState(() => _defaultCurrency = v ?? 'ARS'),
                ),
                const SizedBox(height: 16),

                // Día de inicio del mes financiero
                DropdownButtonFormField<int>(
                  value: _monthStartDay,
                  decoration: const InputDecoration(
                    labelText: 'Inicio del mes financiero',
                    border: OutlineInputBorder(),
                  ),
                  items: List.generate(28, (i) => i + 1)
                      .map((d) => DropdownMenuItem(
                            value: d,
                            child: Text('Día $d'),
                          ))
                      .toList(),
                  onChanged: (v) =>
                      setState(() => _monthStartDay = v ?? 1),
                ),
                const SizedBox(height: 32),

                // Cerrar sesión
                OutlinedButton.icon(
                  onPressed: _confirmLogout,
                  icon: const Icon(Icons.logout, color: Colors.red),
                  label: const Text('Cerrar sesión',
                      style: TextStyle(color: Colors.red)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.red),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text.toUpperCase(),
      style: TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        color: Colors.grey[500],
        letterSpacing: 1,
      ),
    );
  }
}
