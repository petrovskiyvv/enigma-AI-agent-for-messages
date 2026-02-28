import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

Color toneColor(BuildContext context, String tone) => switch (tone) {
      'Негатив' => context.colors.negative,
      'Позитив' => context.colors.positive,
      _         => context.colors.neutral,
    };

Color statusColor(BuildContext context, String status) => switch (status) {
      'Новое'    => context.colors.statusNew,
      'В работе' => context.colors.neutral,
      'Закрыто'  => context.colors.accent,
      _          => context.colors.textSecondary,
    };

String formatDate(String iso) {
  try {
    final dt = DateTime.parse(iso);
    final d  = dt.day.toString().padLeft(2, '0');
    final mo = dt.month.toString().padLeft(2, '0');
    final h  = dt.hour.toString().padLeft(2, '0');
    final mi = dt.minute.toString().padLeft(2, '0');
    return '$d.$mo.${dt.year}\n$h:$mi';
  } catch (_) {
    return iso;
  }
}
