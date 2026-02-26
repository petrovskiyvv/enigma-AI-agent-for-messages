import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class FilterDropdown extends StatelessWidget {
  const FilterDropdown({
    super.key,
    required this.hint,
    required this.items,
    required this.value,
    required this.onChanged,
  });

  final String hint;
  final List<String> items;
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 36,
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          hint: Text(hint, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          dropdownColor: AppColors.card,
          borderRadius: BorderRadius.circular(8),
          style: const TextStyle(color: AppColors.text, fontSize: 12),
          icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.textSecondary, size: 16),
          items: items
              .map((s) => DropdownMenuItem(value: s, child: Text(s)))
              .toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
