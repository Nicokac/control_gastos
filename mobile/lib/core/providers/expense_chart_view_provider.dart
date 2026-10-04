import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _kExpenseChartViewKey = 'expense_chart_view_mode';

enum ExpenseChartViewMode { percentage, amount }

class ExpenseChartViewNotifier extends Notifier<ExpenseChartViewMode> {
  @override
  ExpenseChartViewMode build() {
    _loadFromPrefs();
    return ExpenseChartViewMode.percentage;
  }

  Future<void> _loadFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_kExpenseChartViewKey);
    if (saved == ExpenseChartViewMode.amount.name) {
      state = ExpenseChartViewMode.amount;
    }
  }

  Future<void> setMode(ExpenseChartViewMode mode) async {
    state = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kExpenseChartViewKey, mode.name);
  }
}

final expenseChartViewProvider =
    NotifierProvider<ExpenseChartViewNotifier, ExpenseChartViewMode>(
  ExpenseChartViewNotifier.new,
);
