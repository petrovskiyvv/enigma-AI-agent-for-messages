// TODO Implement this library.// lib/features/knowledge/presentation/file_picker_interface.dart
//
// Условный импорт: на web подключается file_picker_web.dart,
// на остальных платформах — file_picker_mobile.dart
import 'dart:typed_data';
import 'package:flutter/material.dart';

// ignore: uri_does_not_exist
export 'file_picker_mobile.dart'
    if (dart.library.html) 'file_picker_web.dart';

// Общая сигнатура функции — реализуется в каждом файле
typedef PickFileFn = Future<void> Function(
  BuildContext context,
  Future<void> Function(Uint8List bytes, String filename) onUpload,
);
