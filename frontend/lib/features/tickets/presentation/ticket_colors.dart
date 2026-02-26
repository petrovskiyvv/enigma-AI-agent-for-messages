import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

Color toneColor(String tone) => switch (tone) {
      'Негатив' => AppColors.negative,
      'Позитив' => AppColors.positive,
      _ => AppColors.neutral,
    };

Color statusColor(String status) => switch (status) {
      'Новое'    => AppColors.statusNew,
      'В работе' => AppColors.neutral,
      'Закрыто'  => AppColors.accent,
      _ => AppColors.textSecondary,
    };

String formatDate(String iso) {
  try {
    final dt = DateTime.parse(iso);
    final d = dt.day.toString().padLeft(2, '0');
    final mo = dt.month.toString().padLeft(2, '0');
    final h = dt.hour.toString().padLeft(2, '0');
    final mi = dt.minute.toString().padLeft(2, '0');
    return '$d.$mo.${dt.year}\n$h:$mi';
  } catch (_) {
    return iso;
  }
}
