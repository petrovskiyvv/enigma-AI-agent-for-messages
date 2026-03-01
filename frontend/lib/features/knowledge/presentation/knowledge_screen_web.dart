// knowledge_screen_web.dart
// Реализация file picker для web через dart:html
// Подключается через conditional import в knowledge_screen.dart

// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:typed_data';
import 'package:flutter/material.dart';

void pickWebFile(
  BuildContext context,
  Future<void> Function(Uint8List bytes, String filename) onUpload,
) {
  final input = html.FileUploadInputElement()
    ..accept = '.txt,.docx,.pdf'
    ..multiple = false;

  input.onChange.listen((event) async {
    final file = input.files?.first;
    if (file == null) return;

    final reader = html.FileReader();
    reader.readAsArrayBuffer(file);

    reader.onLoad.listen((_) {
      final bytes = reader.result as List<int>;
      onUpload(Uint8List.fromList(bytes), file.name);
    });
  });

  input.click();
}
