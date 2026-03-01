import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'dart:convert';

import '../../../core/theme/app_theme.dart';
import '../../../core/network/api_client.dart';
import 'file_picker_interface.dart';

// ── Репозиторий ──────────────────────────────────────────────────────────────

class _KnowledgeDoc {
  const _KnowledgeDoc({
    required this.source,
    required this.chunks,
    required this.uploadedAt,
  });

  final String source;
  final int chunks;
  final String uploadedAt;

  factory _KnowledgeDoc.fromJson(Map<String, dynamic> j) => _KnowledgeDoc(
    source:     j['source'] as String,
    chunks:     j['chunks'] as int,
    uploadedAt: j['uploaded_at'] as String? ?? '',
  );
}

class _KnowledgeRepository {
  Future<List<_KnowledgeDoc>> fetchAll() async {
    final data = await apiClient.get('/api/knowledge') as List;
    return data
        .map((e) => _KnowledgeDoc.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> uploadBytes({
    required Uint8List bytes,
    required String filename,
  }) async {
    final uri = Uri.parse('${apiClient.baseUrl}/api/knowledge/upload');
    final ext = filename.split('.').last.toLowerCase();
    final mediaTypes = {
      'pdf':  'application/pdf',
      'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'txt':  'text/plain',
    };

    final req = http.MultipartRequest('POST', uri)
      ..files.add(http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: filename,
        contentType: MediaType.parse(mediaTypes[ext] ?? 'application/octet-stream'),
      ));

    final streamed = await req.send();
    final body = await streamed.stream.bytesToString();
    final json = jsonDecode(body) as Map<String, dynamic>;
    if (streamed.statusCode >= 400) {
      throw Exception(json['detail'] ?? 'Ошибка загрузки');
    }
    return json;
  }

  Future<void> delete(String source) async {
    final encoded = Uri.encodeComponent(source);
    await apiClient.delete('/api/knowledge/$encoded');
  }
}

final _repo = _KnowledgeRepository();

// ── Экран ────────────────────────────────────────────────────────────────────

class KnowledgeScreen extends StatefulWidget {
  const KnowledgeScreen({super.key});

  @override
  State<KnowledgeScreen> createState() => _KnowledgeScreenState();
}

class _KnowledgeScreenState extends State<KnowledgeScreen> {
  List<_KnowledgeDoc> _docs = [];
  bool _loading = true;
  String? _error;
  String? _uploadStatus;
  bool _uploading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final docs = await _repo.fetchAll();
      setState(() => _docs = docs);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _pickAndUpload() async {
    // Web: используем input[type=file] через dart:html
    // ignore: avoid_web_libraries_in_flutter
    final input = _createFileInput();
    input.click();
    await _waitForFile(input);
  }

  // Web file picker через dart:html
  dynamic _createFileInput() {
    // ignore: undefined_prefixed_name
    final input = _webFileInput();
    return input;
  }

  // Stub — реальный код ниже через conditional import
  dynamic _webFileInput() {
    throw UnimplementedError('Используй web-сборку');
  }

  Future<void> _waitForFile(dynamic input) async {}

  /// Вызывается когда файл выбран (bytes + filename)
  Future<void> _upload(Uint8List bytes, String filename) async {
    setState(() { _uploading = true; _uploadStatus = null; });
    try {
      final result = await _repo.uploadBytes(bytes: bytes, filename: filename);
      setState(() => _uploadStatus =
      '✅ ${result['source']} — создано ${result['chunks']} фрагментов');
      await _load();
    } catch (e) {
      setState(() => _uploadStatus = '❌ Ошибка: $e');
    } finally {
      setState(() => _uploading = false);
    }
  }

  Future<void> _delete(_KnowledgeDoc doc) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => _ConfirmDialog(
        title: 'Удалить документ?',
        message: '«${doc.source}» (${doc.chunks} фрагм.) будет удалён из базы знаний.',
      ),
    );
    if (confirmed != true) return;
    try {
      await _repo.delete(doc.source);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(context),
        Expanded(child: _buildBody(context)),
      ],
    );
  }

  Widget _buildHeader(BuildContext context) {
    final colors = context.colors;
    return Container(
      color: colors.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(28, 20, 28, 20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: colors.accentDim,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(Icons.library_books_rounded,
                      color: colors.accent, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('База знаний',
                          style: TextStyle(
                            color: colors.text,
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                          )),
                      Text('Документы для обучения AI-ассистента',
                          style: TextStyle(
                              color: colors.textSecondary, fontSize: 11)),
                    ],
                  ),
                ),
                _UploadButton(
                  uploading: _uploading,
                  onUpload: _upload,
                ),
              ],
            ),
          ),
          if (_uploadStatus != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 0, 28, 12),
              child: _StatusBanner(message: _uploadStatus!),
            ),
          Divider(height: 1, color: colors.border),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final colors = context.colors;

    if (_loading) {
      return Center(child: CircularProgressIndicator(color: colors.accent));
    }
    if (_error != null) {
      return Center(
        child: Text(_error!, style: TextStyle(color: colors.negative)),
      );
    }
    if (_docs.isEmpty) {
      return _EmptyState(onUpload: _upload);
    }

    return ListView.separated(
      padding: const EdgeInsets.all(24),
      itemCount: _docs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, i) => _DocCard(
        doc: _docs[i],
        onDelete: () => _delete(_docs[i]),
      ),
    );
  }
}

// ── Кнопка загрузки (Web file picker) ────────────────────────────────────────

class _UploadButton extends StatelessWidget {
  const _UploadButton({required this.uploading, required this.onUpload});

  final bool uploading;
  final Future<void> Function(Uint8List bytes, String filename) onUpload;

  void _pick(BuildContext context) {
    // Web: создаём <input type="file"> и слушаем событие
    // Используем js interop через HtmlElementView или universal_html
    _pickWebFile(context, onUpload);
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return ElevatedButton.icon(
      onPressed: uploading ? null : () => _pick(context),
      icon: uploading
          ? SizedBox(
        width: 14, height: 14,
        child: CircularProgressIndicator(
            strokeWidth: 2, color: colors.bg),
      )
          : const Icon(Icons.upload_file_rounded, size: 16),
      label: Text(uploading ? 'Загружаю...' : 'Загрузить документ'),
      style: ElevatedButton.styleFrom(
        backgroundColor: colors.accent,
        foregroundColor: colors.bg,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(9)),
      ),
    );
  }
}

/// Web file picker — работает только в браузере
void _pickWebFile(
    BuildContext context,
    Future<void> Function(Uint8List, String) onUpload,
    ) {
  // Делегируем платформо-специфичной реализации:
  // web → file_picker_web.dart (dart:html)
  // mobile/desktop → file_picker_mobile.dart (file_picker пакет)
  pickFile(context, onUpload);
}

// ── Карточка документа ────────────────────────────────────────────────────────

class _DocCard extends StatelessWidget {
  const _DocCard({required this.doc, required this.onDelete});

  final _KnowledgeDoc doc;
  final VoidCallback onDelete;

  IconData _iconFor(String source) {
    final ext = source.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':  return Icons.picture_as_pdf_rounded;
      case 'docx': return Icons.description_rounded;
      default:     return Icons.text_snippet_rounded;
    }
  }

  Color _colorFor(BuildContext context, String source) {
    final ext = source.split('.').last.toLowerCase();
    final colors = context.colors;
    switch (ext) {
      case 'pdf':  return colors.negative;
      case 'docx': return colors.accent;
      default:     return colors.neutral;
    }
  }

  String _formatDate(String iso) {
    if (iso.isEmpty) return '—';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day.toString().padLeft(2, '0')}.${dt.month.toString().padLeft(2, '0')}.${dt.year}';
    } catch (_) {
      return iso.substring(0, 10);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final iconColor = _colorFor(context, doc.source);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: colors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(_iconFor(doc.source), color: iconColor, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  doc.source,
                  style: TextStyle(
                      color: colors.text,
                      fontWeight: FontWeight.w600,
                      fontSize: 13),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    _Chip(
                      label: '${doc.chunks} фрагм.',
                      icon: Icons.auto_awesome,
                      color: colors.accent,
                    ),
                    const SizedBox(width: 8),
                    _Chip(
                      label: _formatDate(doc.uploadedAt),
                      icon: Icons.calendar_today_outlined,
                      color: colors.textSecondary,
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: onDelete,
            icon: Icon(Icons.delete_outline_rounded,
                color: colors.negative.withOpacity(0.7), size: 20),
            tooltip: 'Удалить',
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, required this.icon, required this.color});

  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 10, color: color),
        const SizedBox(width: 4),
        Text(label,
            style: TextStyle(color: color, fontSize: 11)),
      ],
    );
  }
}

// ── Пустое состояние ──────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onUpload});

  final Future<void> Function(Uint8List, String) onUpload;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: colors.accentDim,
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.library_add_outlined,
                size: 40, color: colors.accent),
          ),
          const SizedBox(height: 20),
          Text('База знаний пуста',
              style: TextStyle(
                  color: colors.text,
                  fontWeight: FontWeight.w600,
                  fontSize: 16)),
          const SizedBox(height: 8),
          Text(
            'Загрузите документы (.docx, .pdf, .txt),\nчтобы AI мог давать точные ответы',
            textAlign: TextAlign.center,
            style: TextStyle(color: colors.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 24),
          _SupportedFormats(),
        ],
      ),
    );
  }
}

class _SupportedFormats extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final formats = [
      (Icons.picture_as_pdf_rounded, '.PDF', colors.negative),
      (Icons.description_rounded, '.DOCX', colors.accent),
      (Icons.text_snippet_rounded, '.TXT', colors.neutral),
    ];
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: formats.map((f) {
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 6),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: f.$3.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: f.$3.withOpacity(0.3)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(f.$1, color: f.$3, size: 14),
              const SizedBox(width: 6),
              Text(f.$2,
                  style: TextStyle(
                      color: f.$3,
                      fontSize: 12,
                      fontWeight: FontWeight.w600)),
            ],
          ),
        );
      }).toList(),
    );
  }
}

// ── Диалог подтверждения удаления ─────────────────────────────────────────────

class _ConfirmDialog extends StatelessWidget {
  const _ConfirmDialog({required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AlertDialog(
      backgroundColor: colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: colors.border),
      ),
      title: Text(title,
          style: TextStyle(color: colors.text, fontWeight: FontWeight.bold)),
      content: Text(message,
          style: TextStyle(color: colors.textSecondary, fontSize: 13)),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text('Отмена',
              style: TextStyle(color: colors.textSecondary)),
        ),
        ElevatedButton(
          onPressed: () => Navigator.pop(context, true),
          style: ElevatedButton.styleFrom(
            backgroundColor: colors.negative,
            foregroundColor: colors.bg,
          ),
          child: const Text('Удалить'),
        ),
      ],
    );
  }
}

// ── Баннер статуса загрузки ───────────────────────────────────────────────────

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final isError = message.startsWith('❌');
    final color = isError ? colors.negative : colors.accent;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        message,
        style: TextStyle(color: color, fontSize: 13),
      ),
    );
  }
}