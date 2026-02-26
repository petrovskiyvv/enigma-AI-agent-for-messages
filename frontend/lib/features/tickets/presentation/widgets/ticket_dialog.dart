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
    final t = widget.ticket;
    return Dialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.border),
      ),
      child: SizedBox(
        width: 860,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildHeader(t),
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildMetaGrid(t),
                    if (t.originalText.isNotEmpty) ...[
                      const SizedBox(height: 20),
                      _buildOriginalText(t.originalText),
                    ],
                    const SizedBox(height: 20),
                    _buildResponseEditor(),
                    const SizedBox(height: 20),
                    _buildFooter(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(Ticket t) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Text(
            'Обращение #${t.id}',
            style: const TextStyle(color: AppColors.text, fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(width: 16),
          StatusBadge(text: t.emotionalTone, color: toneColor(t.emotionalTone)),
          const SizedBox(width: 8),
          StatusBadge(text: t.category, color: AppColors.accent),
          const Spacer(),
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.close, color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildMetaGrid(Ticket t) {
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
      children: fields
          .map((f) => SizedBox(
                width: 240,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(f.$1, style: const TextStyle(color: AppColors.textSecondary, fontSize: 10, letterSpacing: 0.5)),
                    const SizedBox(height: 3),
                    Text(
                      f.$2.isNotEmpty ? f.$2 : '—',
                      style: const TextStyle(color: AppColors.text, fontSize: 13),
                    ),
                  ],
                ),
              ))
          .toList(),
    );
  }

  Widget _buildOriginalText(String text) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Исходное письмо', style: TextStyle(color: AppColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.border),
          ),
          child: Text(text, style: const TextStyle(color: AppColors.text, fontSize: 13, height: 1.6)),
        ),
      ],
    );
  }

  Widget _buildResponseEditor() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Черновик ответа', style: TextStyle(color: AppColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        TextField(
          controller: _responseCtrl,
          maxLines: 8,
          style: const TextStyle(color: AppColors.text, fontSize: 13, height: 1.6),
          decoration: InputDecoration(
            filled: true,
            fillColor: AppColors.card,
            border: _border(AppColors.border),
            enabledBorder: _border(AppColors.border),
            focusedBorder: _border(AppColors.accent),
          ),
        ),
      ],
    );
  }

  Widget _buildFooter() {
    return Row(
      children: [
        const Text('Статус:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
        const SizedBox(width: 12),
        DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: _status,
            dropdownColor: AppColors.card,
            style: const TextStyle(color: AppColors.text, fontSize: 13),
            items: ['Новое', 'В работе', 'Закрыто']
                .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                .toList(),
            onChanged: (v) => setState(() => _status = v!),
          ),
        ),
        const Spacer(),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Отмена', style: TextStyle(color: AppColors.textSecondary)),
        ),
        const SizedBox(width: 10),
        ElevatedButton.icon(
          onPressed: _saving ? null : _save,
          icon: _saving
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.bg),
                )
              : const Icon(Icons.save_rounded, size: 16),
          label: const Text('Сохранить'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.accent,
            foregroundColor: AppColors.bg,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          ),
        ),
      ],
    );
  }

  OutlineInputBorder _border(Color color) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: color),
      );
}
