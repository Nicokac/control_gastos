import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kAmountsHiddenKey = 'dashboard_amounts_hidden';

class AmountsVisibilityNotifier extends Notifier<bool> {
  @override
  bool build() {
    _loadFromPrefs();
    return false;
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool(_kAmountsHiddenKey) ?? false;
  }

  Future<void> toggle() async {
    state = !state;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kAmountsHiddenKey, state);
  }
}

final amountsHiddenProvider =
    NotifierProvider<AmountsVisibilityNotifier, bool>(
  AmountsVisibilityNotifier.new,
);
