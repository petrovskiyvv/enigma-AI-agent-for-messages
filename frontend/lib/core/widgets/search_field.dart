import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SearchField extends StatelessWidget {
  const SearchField({super.key, required this.onChanged, this.hint});

  final ValueChanged<String> onChanged;
  final String? hint;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return SizedBox(
      height: 36,
      child: TextField(
        style: TextStyle(color: colors.text, fontSize: 13),
        onChanged: onChanged,
        decoration: InputDecoration(
          hintText: hint ?? 'Поиск...',
          hintStyle: TextStyle(color: colors.textSecondary, fontSize: 13),
          prefixIcon: Icon(Icons.search, color: colors.textSecondary, size: 16),
          filled: true,
          fillColor: colors.card,
          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
          border:        _border(colors.border),
          enabledBorder: _border(colors.border),
          focusedBorder: _border(colors.accent),
        ),
      ),
    );
  }

  OutlineInputBorder _border(Color color) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: color),
      );
}
