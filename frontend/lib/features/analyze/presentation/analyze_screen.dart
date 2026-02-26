import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/status_badge.dart';
import '../../tickets/domain/ticket.dart';
import '../../tickets/presentation/ticket_colors.dart';

class AnalyzeRepository {
  const AnalyzeRepository(this._client);
  final ApiClient _client;

  Future<Ticket> analyze(String text) async {
    final data = await _client.post('/api/analyze', {'text': text});
    return Ticket.fromJson(data as Map<String, dynamic>);
  }
}

final _repo = AnalyzeRepository(apiClient);

class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key, required this.onTicketCreated});

  final VoidCallback onTicketCreated;

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  final _ctrl = TextEditingController();
  Ticket? _result;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _analyze() async {
    if (_ctrl.text.trim().isEmpty) return;
    setState(() { _loading = true; _error = null; _result = null; });
    try {
      final ticket = await _repo.analyze(_ctrl.text);
      setState(() => _result = ticket);
      widget.onTicketCreated();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 5, child: _buildInput()),
        Container(width: 1, color: AppColors.border),
        Expanded(flex: 5, child: _buildOutput()),
      ],
    );
  }

  Widget _buildInput() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Текст письма', style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          Expanded(
            child: TextField(
              controller: _ctrl,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              style: const TextStyle(color: AppColors.text, fontSize: 13, height: 1.7),
              decoration: InputDecoration(
                hintText: 'Вставьте текст письма...',
                hintStyle: const TextStyle(color: AppColors.textSecondary),
                filled: true,
                fillColor: AppColors.card,
                contentPadding: const EdgeInsets.all(16),
                border: _border(AppColors.border),
                enabledBorder: _border(AppColors.border),
                focusedBorder: _border(AppColors.accent),
              ),
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _loading ? null : _analyze,
              icon: _loading
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.bg))
                  : const Icon(Icons.auto_awesome_rounded, size: 16),
              label: Text(_loading ? 'Анализирую...' : 'Анализировать письмо'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accent,
                foregroundColor: AppColors.bg,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOutput() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: _error != null
          ? Text(_error!, style: const TextStyle(color: AppColors.negative))
          : _result == null
              ? const Center(
                  child: Text('Результат появится здесь', style: TextStyle(color: AppColors.textSecondary)),
                )
              : _buildResult(_result!),
    );
  }

  Widget _buildResult(Ticket t) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const Icon(Icons.check_circle, color: AppColors.accent, size: 18),
            const SizedBox(width: 8),
            const Text('Тикет создан!', style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            Text('#${t.id}', style: const TextStyle(color: AppColors.textSecondary)),
          ]),
          const SizedBox(height: 20),
          _card('Извлечённые данные', [
            if (t.fullName.isNotEmpty) _row('ФИО', t.fullName),
            if (t.email.isNotEmpty) _row('Email', t.email),
            if (t.phone.isNotEmpty) _row('Телефон', t.phone),
            if (t.deviceNumbers.isNotEmpty) _row('Приборы', t.deviceNumbers),
            _row('Суть', t.issueSummary.isEmpty ? '—' : t.issueSummary),
          ]),
          const SizedBox(height: 16),
          _card('AI-классификация', [
            Row(children: [
              const Text('Тональность:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
              const SizedBox(width: 10),
              StatusBadge(text: t.emotionalTone, color: toneColor(t.emotionalTone)),
            ]),
            const SizedBox(height: 8),
            Row(children: [
              const Text('Категория:', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
              const SizedBox(width: 10),
              StatusBadge(text: t.category, color: AppColors.accent),
            ]),
          ]),
          if (t.aiResponse.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Черновик ответа', style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.border),
              ),
              child: SelectableText(t.aiResponse, style: const TextStyle(color: AppColors.text, fontSize: 13, height: 1.7)),
            ),
          ],
        ],
      ),
    );
  }

  Widget _card(String title, List<Widget> children) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(color: AppColors.textSecondary, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 80, child: Text('$label:', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12))),
          Expanded(child: Text(value, style: const TextStyle(color: AppColors.text, fontSize: 13))),
        ],
      ),
    );
  }

  OutlineInputBorder _border(Color color) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: color),
      );
}
