import 'package:flutter/material.dart';

@immutable
class AppColors extends ThemeExtension<AppColors> {
  const AppColors({
    required this.bg,
    required this.surface,
    required this.card,
    required this.border,
    required this.accent,
    required this.accentDim,
    required this.text,
    required this.textSecondary,
    required this.negative,
    required this.positive,
    required this.neutral,
    required this.statusNew,
  });

  final Color bg;
  final Color surface;
  final Color card;
  final Color border;
  final Color accent;
  final Color accentDim;
  final Color text;
  final Color textSecondary;
  final Color negative;
  final Color positive;
  final Color neutral;
  final Color statusNew;

  static const dark = AppColors(
    bg:            Color(0xFF0F1117),
    surface:       Color(0xFF1A1D27),
    card:          Color(0xFF21253A),
    border:        Color(0xFF2E3350),
    accent:        Color(0xFF00D4AA),
    accentDim:     Color(0x2600D4AA),
    text:          Color(0xFFE8EAF0),
    textSecondary: Color(0xFF8B90A8),
    negative:      Color(0xFFFF4D6D),
    positive:      Color(0xFF00D4AA),
    neutral:       Color(0xFFFFB938),
    statusNew:     Color(0xFF4D9FFF),
  );

  static const light = AppColors(
    bg:            Color(0xFFF4F6FA),
    surface:       Color(0xFFFFFFFF),
    card:          Color(0xFFEEF1F8),
    border:        Color(0xFFD1D9EC),
    accent:        Color(0xFF00A88A),
    accentDim:     Color(0x1A00A88A),
    text:          Color(0xFF1A1D27),
    textSecondary: Color(0xFF6B7280),
    negative:      Color(0xFFE02D4B),
    positive:      Color(0xFF00A88A),
    neutral:       Color(0xFFD97706),
    statusNew:     Color(0xFF2563EB),
  );

  @override
  AppColors copyWith({
    Color? bg, Color? surface, Color? card, Color? border,
    Color? accent, Color? accentDim, Color? text, Color? textSecondary,
    Color? negative, Color? positive, Color? neutral, Color? statusNew,
  }) => AppColors(
    bg:            bg            ?? this.bg,
    surface:       surface       ?? this.surface,
    card:          card          ?? this.card,
    border:        border        ?? this.border,
    accent:        accent        ?? this.accent,
    accentDim:     accentDim     ?? this.accentDim,
    text:          text          ?? this.text,
    textSecondary: textSecondary ?? this.textSecondary,
    negative:      negative      ?? this.negative,
    positive:      positive      ?? this.positive,
    neutral:       neutral       ?? this.neutral,
    statusNew:     statusNew     ?? this.statusNew,
  );

  @override
  AppColors lerp(AppColors? other, double t) {
    if (other == null) return this;
    return AppColors(
      bg:            Color.lerp(bg,            other.bg,            t)!,
      surface:       Color.lerp(surface,       other.surface,       t)!,
      card:          Color.lerp(card,          other.card,          t)!,
      border:        Color.lerp(border,        other.border,        t)!,
      accent:        Color.lerp(accent,        other.accent,        t)!,
      accentDim:     Color.lerp(accentDim,     other.accentDim,     t)!,
      text:          Color.lerp(text,          other.text,          t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      negative:      Color.lerp(negative,      other.negative,      t)!,
      positive:      Color.lerp(positive,      other.positive,      t)!,
      neutral:       Color.lerp(neutral,       other.neutral,       t)!,
      statusNew:     Color.lerp(statusNew,     other.statusNew,     t)!,
    );
  }
}

extension AppColorsX on BuildContext {
  AppColors get colors => Theme.of(this).extension<AppColors>()!;
}

abstract final class AppTheme {
  static ThemeData build(AppColors colors) => ThemeData(
    brightness: colors == AppColors.dark ? Brightness.dark : Brightness.light,
    scaffoldBackgroundColor: colors.bg,
    fontFamily: 'monospace',
    colorScheme: ColorScheme(
      brightness: colors == AppColors.dark ? Brightness.dark : Brightness.light,
      primary:    colors.accent,
      onPrimary:  colors.bg,
      secondary:  colors.accent,
      onSecondary: colors.bg,
      error:      colors.negative,
      onError:    colors.bg,
      surface:    colors.surface,
      onSurface:  colors.text,
    ),
    dividerColor: colors.border,
    extensions: [colors],
  );

  static ThemeData get dark  => build(AppColors.dark);
  static ThemeData get light => build(AppColors.light);
}
