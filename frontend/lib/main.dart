import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/tickets/presentation/app_shell.dart';

void main() => runApp(const EnigmaApp());

class EnigmaApp extends StatelessWidget {
  const EnigmaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ЭРИС — Техподдержка',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      home: const AppShell(),
    );
  }
}
