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
    final colors = context.colors;
    return SizedBox(
      height: 36,
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          hint: Text(hint, style: TextStyle(color: colors.textSecondary, fontSize: 12)),
          dropdownColor: colors.card,
          borderRadius: BorderRadius.circular(8),
          style: TextStyle(color: colors.text, fontSize: 12),
          icon: Icon(Icons.keyboard_arrow_down, color: colors.textSecondary, size: 16),
          items: items.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
