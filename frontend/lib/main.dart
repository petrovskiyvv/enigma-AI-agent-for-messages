import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/tickets/presentation/app_shell.dart';

void main() => runApp(const EnigmaApp());

class EnigmaApp extends StatefulWidget {
  const EnigmaApp({super.key});

  // Глобальный ключ позволяет вызвать toggleTheme() из любого места дерева
  static _EnigmaAppState of(BuildContext context) =>
      context.findAncestorStateOfType<_EnigmaAppState>()!;

  @override
  State<EnigmaApp> createState() => _EnigmaAppState();
}

class _EnigmaAppState extends State<EnigmaApp> {
  ThemeMode _themeMode = ThemeMode.dark;

  bool get isDark => _themeMode == ThemeMode.dark;

  void toggleTheme() => setState(
      () => _themeMode = isDark ? ThemeMode.light : ThemeMode.dark);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ЭРИС — Техподдержка',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: _themeMode,
      home: const AppShell(),
    );
  }
}
