// lib/features/knowledge/presentation/file_picker_web.dart
// Реализация для web через dart:html — без внешних плагинов
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';

Future<void> pickFile(
  BuildContext context,
  Future<void> Function(Uint8List bytes, String filename) onUpload,
) async {
  final completer = Completer<void>();

  final input = html.FileUploadInputElement()
    ..accept = '.pdf,.docx,.txt'
    ..multiple = false;

  input.onChange.listen((event) async {
    final file = input.files?.first;
    if (file == null) {
      completer.complete();
      return;
    }

    final reader = html.FileReader();
    reader.readAsArrayBuffer(file);

    reader.onLoad.listen((_) async {
      try {
        final bytes = Uint8List.fromList(reader.result as List<int>);
        await onUpload(bytes, file.name);
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Ошибка загрузки: $e')),
          );
        }
      } finally {
        if (!completer.isCompleted) completer.complete();
      }
    });

    reader.onError.listen((_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ошибка чтения файла')),
        );
      }
      if (!completer.isCompleted) completer.complete();
    });
  });

  input.click();
  await completer.future;
}
