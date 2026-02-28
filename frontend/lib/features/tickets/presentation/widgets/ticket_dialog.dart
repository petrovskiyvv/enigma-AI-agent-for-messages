import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/status_badge.dart';
import '../../data/ticket_repository.dart';
import '../../domain/ticket.dart';
import '../ticket_colors.dart';

class TicketDialog extends StatefulWidget {
  const TicketDialog({super.key, required this.ticket, required this.onSaved});

  final Ticket ticket;
  final VoidCallback onSaved;

  @override
  State<TicketDialog> createState() => _TicketDialogState();
}

class _TicketDialogState extends State<TicketDialog> {
  late final TextEditingController _responseCtrl;
  late String _status;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _responseCtrl = TextEditingController(text: widget.ticket.aiResponse);
    _status = widget.ticket.status;
  }

  @override
  void dispose() {
    _responseCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    await ticketRepository.update(
      widget.ticket.id,
      aiResponse: _responseCtrl.text,
      status: _status,
    );
    widget.onSaved();
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final t = widget.ticket;
    final screenWidth = MediaQuery.of(context).size.width;
    final isMobile = screenWidth < 600;
    return Dialog(
      backgroundColor: colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: colors.border),
      ),
      child: SizedBox(
        width: isMobile ? screenWidth * 0.95 : 860,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildHeader(context, t),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildMetaGrid(context, t),
                    if (t.originalText.isNotEmpty) ...[
                      const SizedBox(height: 20),
                      _buildOriginalText(context, t.originalText),
                    ],
                    const SizedBox(height: 20),
                    _buildResponseEditor(context),
                    const SizedBox(height: 20),
                    _buildFooter(context),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, Ticket t) {
    final colors = context.colors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: colors.card,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
        border: Border(bottom: BorderSide(color: colors.border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Обращение #${t.id}',
                  style: TextStyle(color: colors.text, fontWeight: FontWeight.bold, fontSize: 15),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: [
                    StatusBadge(text: t.emotionalTone, color: toneColor(context, t.emotionalTone)),
                    StatusBadge(text: t.category, color: colors.accent),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: Icon(Icons.close, color: colors.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildMetaGrid(BuildContext context, Ticket t) {
    final colors = context.colors;
    final fields = [
      ('ФИО', t.fullName),
      ('Объект', t.facility),
      ('Телефон', t.phone),
      ('Email', t.email),
      ('Заводские номера', t.deviceNumbers),
      ('Тип прибора', t.deviceType),
    ];
    return Wrap(
      spacing: 16,
      runSpacing: 12,
      children: fields.map((f) => SizedBox(
        width: 200,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(f.$1, style: TextStyle(color: colors.textSecondary, fontSize: 10, letterSpacing: 0.5)),
            const SizedBox(height: 3),
            Text(
              f.$2.isNotEmpty ? f.$2 : '—',
              style: TextStyle(color: colors.text, fontSize: 13),
            ),
          ],
        ),
      )).toList(),
    );
  }

  Widget _buildOriginalText(BuildContext context, String text) {
    final colors = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Исходное письмо', style: TextStyle(color: colors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: colors.card,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: colors.border),
          ),
          child: Text(text, style: TextStyle(color: colors.text, fontSize: 13, height: 1.6)),
        ),
      ],
    );
  }

  Widget _buildResponseEditor(BuildContext context) {
    final colors = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Черновик ответа', style: TextStyle(color: colors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        TextField(
          controller: _responseCtrl,
          maxLines: 8,
          style: TextStyle(color: colors.text, fontSize: 13, height: 1.6),
          decoration: InputDecoration(
            filled: true,
            fillColor: colors.card,
            border:        _border(colors.border),
            enabledBorder: _border(colors.border),
            focusedBorder: _border(colors.accent),
          ),
        ),
      ],
    );
  }

  Widget _buildFooter(BuildContext context) {
    final colors = context.colors;
    final saveButton = ElevatedButton.icon(
      onPressed: _saving ? null : _save,
      icon: _saving
          ? SizedBox(
        width: 14, height: 14,
        child: CircularProgressIndicator(strokeWidth: 2, color: colors.bg),
      )
          : const Icon(Icons.save_rounded, size: 16),
      label: const Text('Сохранить'),
      style: ElevatedButton.styleFrom(
        backgroundColor: colors.accent,
        foregroundColor: colors.bg,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      ),
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Text('Статус:', style: TextStyle(color: colors.textSecondary, fontSize: 13)),
            const SizedBox(width: 12),
            DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _status,
                dropdownColor: colors.card,
                style: TextStyle(color: colors.text, fontSize: 13),
                items: ['Новое', 'В работе', 'Закрыто']
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setState(() => _status = v!),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Отмена', style: TextStyle(color: colors.textSecondary)),
            ),
            const SizedBox(width: 10),
            saveButton,
          ],
        ),
      ],
    );
  }

  OutlineInputBorder _border(Color color) => OutlineInputBorder(
    borderRadius: BorderRadius.circular(8),
    borderSide: BorderSide(color: color),
  );
}