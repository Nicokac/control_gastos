import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/repositories/category_rule_repository.dart';

final categoryRuleRepositoryProvider = Provider<CategoryRuleRepository>((ref) {
  return CategoryRuleRepository();
});

final categoryRulesProvider = FutureProvider<List<dynamic>>((ref) {
  return ref.read(categoryRuleRepositoryProvider).getRules();
});
