import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/responsive.dart';
import '../../../core/widgets/status_badge.dart';
import '../../tickets/domain/ticket.dart';
import '../../tickets/presentation/ticket_colors.dart';

class _CreateRepository {
  const _CreateRepository(this._client);
  final ApiClient _client;

  Future<Ticket> create(Map<String, String> fields) async {
    final data = await _client.post('/api/tickets', fields);
    return Ticket.fromJson(data as Map<String, dynamic>);
  }
}

final _repo = _CreateRepository(apiClient);

class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key, required this.onTicketCreated});
  final VoidCallback onTicketCreated;

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> {
  Ticket? _result;
  bool _loading = false;
  String? _error;

  final _fullNameCtrl   = TextEditingController();
  final _facilityCtrl   = TextEditingController();
  final _phoneCtrl      = TextEditingController();
  final _emailCtrl      = TextEditingController();
  final _deviceNumCtrl  = TextEditingController();
  final _deviceTypeCtrl = TextEditingController();
  final _textCtrl       = TextEditingController();

  @override
  void dispose() {
    for (final c in [
      _fullNameCtrl, _facilityCtrl, _phoneCtrl, _emailCtrl,
      _deviceNumCtrl, _deviceTypeCtrl, _textCtrl,
    ]) { c.dispose(); }
    super.dispose();
  }

  Future<void> _submitManual() async {
    if (_textCtrl.text.trim().isEmpty &&
        _fullNameCtrl.text.trim().isEmpty) return;
    setState(() { _loading = true; _error = null; _result = null; });
    try {
      final ticket = await _repo.create({
        'full_name':      _fullNameCtrl.text.trim(),
        'facility':       _facilityCtrl.text.trim(),
        'phone':          _phoneCtrl.text.trim(),
        'email':          _emailCtrl.text.trim(),
        'device_numbers': _deviceNumCtrl.text.trim(),
        'device_type':    _deviceTypeCtrl.text.trim(),
        'original_text':  _textCtrl.text.trim(),
      });
      setState(() => _result = ticket);
      widget.onTicketCreated();
      _clearManualForm();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _fillTestData() {
    _fullNameCtrl.text   = 'Петров Алексей Владимирович';
    _facilityCtrl.text   = 'ОАО «Нефтехим», г. Уфа';
    _phoneCtrl.text      = '+7 (347) 255-10-42';
    _emailCtrl.text      = 'a.petrov@neftekhim.ru';
    _deviceNumCtrl.text  = 'НК-0471, НК-0472';
    _deviceTypeCtrl.text = 'Газоанализатор ГС-812';
    _textCtrl.text       =
        'Добрый день! Обращаюсь по вопросу некорректной работы газоанализаторов ГС-812 '
        '(зав. номера НК-0471 и НК-0472). Приборы установлены на объекте ОАО «Нефтехим» '
        'в г. Уфа. В течение последних двух недель фиксируются ложные срабатывания датчика '
        'CO2 при показаниях ниже порогового значения. Прошу организовать выезд специалиста '
        'для диагностики оборудования или дать рекомендации по устранению неисправности.';
    setState(() {});
  }

  void _clearManualForm() {
    for (final c in [
      _fullNameCtrl, _facilityCtrl, _phoneCtrl, _emailCtrl,
      _deviceNumCtrl, _deviceTypeCtrl, _textCtrl,
    ]) { c.clear(); }
  }

  void _resetResult() => setState(() { _result = null; _error = null; });

  @override
  Widget build(BuildContext context) {
    final mobile = isMobile(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildPageHeader(context, mobile),
        Expanded(
          child: mobile
              ? _buildMobileBody(context)
              : _buildDesktopBody(context),
        ),
      ],
    );
  }

  Widget _buildPageHeader(BuildContext context, bool mobile) {
    final colors = context.colors;
    return Container(
      color: colors.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: EdgeInsets.fromLTRB(mobile ? 16 : 28, 20, 28, 20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: colors.accentDim,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(Icons.add_box_rounded, color: colors.accent, size: 20),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Создать обращение',
                        style: TextStyle(
                          color: colors.text,
                          fontWeight: FontWeight.bold,
                          fontSize: mobile ? 16 : 18,
                        )),
                    Text('Новая заявка в систему поддержки',
                        style: TextStyle(color: colors.textSecondary, fontSize: 11)),
                  ],
                ),
              ],
            ),
          ),
          Divider(height: 1, color: colors.border),
        ],
      ),
    );
  }

  Widget _buildDesktopBody(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 55,
          child: _ManualForm(
            ctrls: _ManualCtrls(
              fullName: _fullNameCtrl, facility: _facilityCtrl,
              phone: _phoneCtrl, email: _emailCtrl,
              deviceNum: _deviceNumCtrl, deviceType: _deviceTypeCtrl,
              text: _textCtrl,
            ),
            loading: _loading,
            onSubmit: _submitManual,
            onFillTest: _fillTestData,
            onReset: _resetResult,
          ),
        ),
        VerticalDivider(width: 1, color: context.colors.border),
        Expanded(
          flex: 45,
          child: _ResultPanel(result: _result, error: _error),
        ),
      ],
    );
  }

  Widget _buildMobileBody(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          _ManualForm(
            ctrls: _ManualCtrls(
              fullName: _fullNameCtrl, facility: _facilityCtrl,
              phone: _phoneCtrl, email: _emailCtrl,
              deviceNum: _deviceNumCtrl, deviceType: _deviceTypeCtrl,
              text: _textCtrl,
            ),
            loading: _loading,
            onSubmit: _submitManual,
            onFillTest: _fillTestData,
            onReset: _resetResult,
            mobile: true,
          ),
          if (_result != null || _error != null) ...[
            Divider(color: context.colors.border),
            _ResultPanel(result: _result, error: _error, mobile: true),
          ],
        ],
      ),
    );
  }
}

// ─── Manual form ─────────────────────────────────────────────────────────────

class _ManualCtrls {
  const _ManualCtrls({
    required this.fullName,
    required this.facility,
    required this.phone,
    required this.email,
    required this.deviceNum,
    required this.deviceType,
    required this.text,
  });
  final TextEditingController fullName;
  final TextEditingController facility;
  final TextEditingController phone;
  final TextEditingController email;
  final TextEditingController deviceNum;
  final TextEditingController deviceType;
  final TextEditingController text;
}

class _ManualForm extends StatelessWidget {
  const _ManualForm({
    required this.ctrls,
    required this.loading,
    required this.onSubmit,
    required this.onFillTest,
    required this.onReset,
    this.mobile = false,
  });

  final _ManualCtrls ctrls;
  final bool loading;
  final VoidCallback onSubmit;
  final VoidCallback onFillTest;
  final VoidCallback onReset;
  final bool mobile;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;

    return SingleChildScrollView(
      padding: EdgeInsets.all(mobile ? 16 : 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Кнопка тестовых данных
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              OutlinedButton.icon(
                onPressed: onFillTest,
                icon: const Icon(Icons.science_outlined, size: 14),
                label: const Text('Тестовые данные',
                    style: TextStyle(fontSize: 12)),
                style: OutlinedButton.styleFrom(
                  foregroundColor: colors.accent,
                  side: BorderSide(color: colors.accent.withOpacity(0.5)),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 8),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          _SectionLabel(
              icon: Icons.person_outline_rounded,
              label: 'Контактные данные'),
          const SizedBox(height: 12),
          if (mobile) ...[
            _Field(
                label: 'ФИО',
                ctrl: ctrls.fullName,
                hint: 'Иванов Иван Иванович'),
            const SizedBox(height: 10),
            _Field(
                label: 'Объект / организация',
                ctrl: ctrls.facility,
                hint: 'ООО «Завод», г. Казань'),
            const SizedBox(height: 10),
            _Field(
                label: 'Телефон',
                ctrl: ctrls.phone,
                hint: '+7 (999) 000-00-00',
                keyboard: TextInputType.phone),
            const SizedBox(height: 10),
            _Field(
                label: 'Email',
                ctrl: ctrls.email,
                hint: 'ivan@company.ru',
                keyboard: TextInputType.emailAddress),
          ] else ...[
            Row(children: [
              Expanded(
                  child: _Field(
                      label: 'ФИО',
                      ctrl: ctrls.fullName,
                      hint: 'Иванов Иван Иванович')),
              const SizedBox(width: 14),
              Expanded(
                  child: _Field(
                      label: 'Объект / организация',
                      ctrl: ctrls.facility,
                      hint: 'ООО «Завод», г. Казань')),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                  child: _Field(
                      label: 'Телефон',
                      ctrl: ctrls.phone,
                      hint: '+7 (999) 000-00-00',
                      keyboard: TextInputType.phone)),
              const SizedBox(width: 14),
              Expanded(
                  child: _Field(
                      label: 'Email',
                      ctrl: ctrls.email,
                      hint: 'ivan@company.ru',
                      keyboard: TextInputType.emailAddress)),
            ]),
          ],

          const SizedBox(height: 20),
          _Divider(),
          const SizedBox(height: 20),
          _SectionLabel(
              icon: Icons.settings_outlined, label: 'Оборудование'),
          const SizedBox(height: 12),
          if (mobile) ...[
            _Field(
                label: 'Заводские номера',
                ctrl: ctrls.deviceNum,
                hint: 'НК-001, НК-002'),
            const SizedBox(height: 10),
            _Field(
                label: 'Тип прибора',
                ctrl: ctrls.deviceType,
                hint: 'Газоанализатор ГС-812'),
          ] else
            Row(children: [
              Expanded(
                  child: _Field(
                      label: 'Заводские номера',
                      ctrl: ctrls.deviceNum,
                      hint: 'НК-001, НК-002')),
              const SizedBox(width: 14),
              Expanded(
                  child: _Field(
                      label: 'Тип прибора',
                      ctrl: ctrls.deviceType,
                      hint: 'Газоанализатор ГС-812')),
            ]),

          const SizedBox(height: 20),
          _Divider(),
          const SizedBox(height: 20),
          _SectionLabel(
              icon: Icons.message_outlined, label: 'Текст обращения'),
          const SizedBox(height: 10),
          _Hint(
              text:
                  'ИИ автоматически определит тональность, категорию и сгенерирует черновик ответа'),
          const SizedBox(height: 10),
          _Field(
            label: '',
            ctrl: ctrls.text,
            hint: 'Опишите суть обращения подробно...',
            maxLines: mobile ? 5 : 6,
            minLines: mobile ? 5 : 6,
          ),

          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: loading ? null : onSubmit,
              icon: loading
                  ? SizedBox(
                      width: 15,
                      height: 15,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: colors.bg),
                    )
                  : const Icon(Icons.add_circle_outline_rounded, size: 16),
              label: Text(loading ? 'Создаю...' : 'Создать обращение'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colors.accent,
                foregroundColor: colors.bg,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Result panel ─────────────────────────────────────────────────────────────

class _ResultPanel extends StatelessWidget {
  const _ResultPanel({this.result, this.error, this.mobile = false});
  final Ticket? result;
  final String? error;
  final bool mobile;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;

    if (error != null) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: _ErrorCard(message: error!),
      );
    }

    if (result == null) return _EmptyState();

    final t = result!;
    return SingleChildScrollView(
      padding: EdgeInsets.all(mobile ? 16 : 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: colors.accent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: colors.accent.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle_rounded,
                    color: colors.accent, size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Обращение создано',
                          style: TextStyle(
                              color: colors.accent,
                              fontWeight: FontWeight.bold,
                              fontSize: 13)),
                      Text('Заявка #${t.id} добавлена в систему',
                          style: TextStyle(
                              color: colors.textSecondary,
                              fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _ResultCard(
            icon: Icons.psychology_outlined,
            title: 'Классификация',
            child: Row(
              children: [
                StatusBadge(
                    text: t.emotionalTone,
                    color: toneColor(context, t.emotionalTone)),
                const SizedBox(width: 8),
                StatusBadge(text: t.category, color: colors.accent),
                const SizedBox(width: 8),
                StatusBadge(
                    text: t.status,
                    color: statusColor(context, t.status)),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _ResultCard(
            icon: Icons.person_outline_rounded,
            title: 'Данные клиента',
            child: Column(
              children: [
                if (t.fullName.isNotEmpty)
                  _DataRow(label: 'ФИО', value: t.fullName),
                if (t.facility.isNotEmpty)
                  _DataRow(label: 'Объект', value: t.facility),
                if (t.phone.isNotEmpty)
                  _DataRow(label: 'Телефон', value: t.phone),
                if (t.email.isNotEmpty)
                  _DataRow(label: 'Email', value: t.email),
                if (t.deviceNumbers.isNotEmpty)
                  _DataRow(label: 'Приборы', value: t.deviceNumbers),
                if (t.deviceType.isNotEmpty)
                  _DataRow(label: 'Тип', value: t.deviceType),
                if (t.fullName.isEmpty &&
                    t.phone.isEmpty &&
                    t.email.isEmpty)
                  Text('—',
                      style: TextStyle(
                          color: colors.textSecondary, fontSize: 13)),
              ],
            ),
          ),
          if (t.issueSummary.isNotEmpty) ...[
            const SizedBox(height: 12),
            _ResultCard(
              icon: Icons.summarize_outlined,
              title: 'Суть обращения',
              child: Text(t.issueSummary,
                  style: TextStyle(
                      color: colors.text, fontSize: 13, height: 1.5)),
            ),
          ],
          if (t.aiResponse.isNotEmpty) ...[
            const SizedBox(height: 12),
            _ResultCard(
              icon: Icons.smart_toy_outlined,
              title: 'Черновик ответа (ИИ)',
              child: SelectableText(
                t.aiResponse,
                style: TextStyle(
                    color: colors.text, fontSize: 12, height: 1.7),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Shared helpers ───────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Row(
      children: [
        Icon(icon, size: 15, color: colors.accent),
        const SizedBox(width: 7),
        Text(label,
            style: TextStyle(
                color: colors.text,
                fontSize: 13,
                fontWeight: FontWeight.w600)),
      ],
    );
  }
}

class _Hint extends StatelessWidget {
  const _Hint({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: colors.accentDim,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.accent.withOpacity(0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded,
              size: 13, color: colors.accent),
          const SizedBox(width: 7),
          Expanded(
            child: Text(text,
                style: TextStyle(
                    color: colors.textSecondary,
                    fontSize: 11,
                    height: 1.4)),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.label,
    required this.ctrl,
    required this.hint,
    this.maxLines = 1,
    this.minLines = 1,
    this.keyboard = TextInputType.text,
  });

  final String label;
  final TextEditingController ctrl;
  final String hint;
  final int maxLines;
  final int minLines;
  final TextInputType keyboard;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label.isNotEmpty) ...[
          Text(label,
              style: TextStyle(
                  color: colors.textSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 5),
        ],
        TextField(
          controller: ctrl,
          keyboardType: keyboard,
          maxLines: maxLines,
          minLines: minLines,
          style: TextStyle(color: colors.text, fontSize: 13),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
                color: colors.textSecondary.withOpacity(0.5),
                fontSize: 12),
            filled: true,
            fillColor: colors.card,
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 14, vertical: 11),
            border: _border(colors.border),
            enabledBorder: _border(colors.border),
            focusedBorder: _border(colors.accent),
          ),
        ),
      ],
    );
  }

  OutlineInputBorder _border(Color c) => OutlineInputBorder(
        borderRadius: BorderRadius.circular(9),
        borderSide: BorderSide(color: c),
      );
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) =>
      Divider(height: 1, color: context.colors.border);
}

class _ResultCard extends StatelessWidget {
  const _ResultCard(
      {required this.icon,
      required this.title,
      required this.child});
  final IconData icon;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: colors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 13, color: colors.textSecondary),
              const SizedBox(width: 6),
              Text(title,
                  style: TextStyle(
                      color: colors.textSecondary,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5)),
            ],
          ),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }
}

class _DataRow extends StatelessWidget {
  const _DataRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 72,
            child: Text('$label:',
                style: TextStyle(
                    color: colors.textSecondary, fontSize: 12)),
          ),
          Expanded(
            child: Text(value,
                style:
                    TextStyle(color: colors.text, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colors.negative.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border:
            Border.all(color: colors.negative.withOpacity(0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline_rounded,
              color: colors.negative, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Ошибка',
                    style: TextStyle(
                        color: colors.negative,
                        fontWeight: FontWeight.bold,
                        fontSize: 13)),
                const SizedBox(height: 4),
                Text(message,
                    style: TextStyle(
                        color: colors.textSecondary,
                        fontSize: 12,
                        height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: colors.accentDim,
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.inbox_outlined,
                size: 36, color: colors.accent),
          ),
          const SizedBox(height: 16),
          Text('Результат появится здесь',
              style: TextStyle(
                  color: colors.text,
                  fontWeight: FontWeight.w600,
                  fontSize: 14)),
          const SizedBox(height: 6),
          Text('Заполните форму и нажмите кнопку создания',
              style: TextStyle(
                  color: colors.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }
}
