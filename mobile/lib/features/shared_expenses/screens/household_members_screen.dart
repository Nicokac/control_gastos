import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/shared_expense_provider.dart';

class HouseholdMembersScreen extends ConsumerStatefulWidget {
  const HouseholdMembersScreen({super.key});

  @override
  ConsumerState<HouseholdMembersScreen> createState() =>
      _HouseholdMembersScreenState();
}

class _HouseholdMembersScreenState
    extends ConsumerState<HouseholdMembersScreen> {
  Future<void> _showAddDialog() async {
    final ctrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Agregar miembro'),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: ctrl,
            autofocus: true,
            decoration: const InputDecoration(
              labelText: 'Nombre',
              border: OutlineInputBorder(),
            ),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Ingresá un nombre' : null,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () async {
              if (!formKey.currentState!.validate()) return;
              Navigator.pop(ctx);
              await _addMember(ctrl.text.trim());
            },
            child: const Text('Agregar'),
          ),
        ],
      ),
    );
    ctrl.dispose();
  }

  Future<void> _addMember(String name) async {
    try {
      await ref.read(sharedExpenseRepositoryProvider).createMember(name);
      ref.invalidate(householdMembersProvider);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al agregar el miembro')),
        );
      }
    }
  }

  Future<void> _confirmDelete(Map<String, dynamic> member) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar miembro'),
        content: Text('¿Eliminar a "${member['name']}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ref
            .read(sharedExpenseRepositoryProvider)
            .deleteMember(member['id'] as int);
        ref.invalidate(householdMembersProvider);
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Error al eliminar el miembro')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final membersAsync = ref.watch(householdMembersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Miembros del hogar'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            tooltip: 'Agregar miembro',
            onPressed: _showAddDialog,
          ),
        ],
      ),
      body: membersAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 12),
              Text(e.toString(),
                  style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.invalidate(householdMembersProvider),
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
        data: (members) => members.isEmpty
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.group_outlined,
                        size: 64, color: Colors.grey),
                    const SizedBox(height: 12),
                    const Text('Sin miembros del hogar',
                        style: TextStyle(color: Colors.grey)),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: _showAddDialog,
                      icon: const Icon(Icons.person_add),
                      label: const Text('Agregar miembro'),
                    ),
                  ],
                ),
              )
            : ListView.separated(
                itemCount: members.length,
                separatorBuilder: (context, index) =>
                    const Divider(height: 1, indent: 16),
                itemBuilder: (context, index) {
                  final member = members[index] as Map<String, dynamic>;
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor:
                          const Color(0xFF0d6efd).withValues(alpha: 0.15),
                      child: Text(
                        (member['name'] as String)
                            .substring(0, 1)
                            .toUpperCase(),
                        style: TextStyle(
                          color: const Color(0xFF0d6efd),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(member['name'] as String),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      color: Colors.grey[400],
                      onPressed: () => _confirmDelete(member),
                    ),
                  );
                },
              ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddDialog,
        backgroundColor: const Color(0xFF0d6efd),
        child: const Icon(Icons.person_add),
      ),
    );
  }
}
