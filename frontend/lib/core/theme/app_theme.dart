import 'package:flutter/material.dart';

abstract final class AppColors {
  static const bg = Color(0xFF0F1117);
  static const surface = Color(0xFF1A1D27);
  static const card = Color(0xFF21253A);
  static const border = Color(0xFF2E3350);

  static const accent = Color(0xFF00D4AA);
  static const accentDim = Color(0x2600D4AA);

  static const text = Color(0xFFE8EAF0);
  static const textSecondary = Color(0xFF8B90A8);

  static const negative = Color(0xFFFF4D6D);
  static const positive = Color(0xFF00D4AA);
  static const neutral = Color(0xFFFFB938);
  static const statusNew = Color(0xFF4D9FFF);
}

abstract final class AppTheme {
  static ThemeData get dark => ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.bg,
        fontFamily: 'monospace',
        colorScheme: const ColorScheme.dark(
          primary: AppColors.accent,
          surface: AppColors.surface,
        ),
        dividerColor: AppColors.border,
      );
}
