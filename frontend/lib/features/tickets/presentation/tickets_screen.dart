import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/filter_dropdown.dart';
import '../../../core/widgets/search_field.dart';
import '../data/ticket_repository.dart';
import '../domain/ticket.dart';
import 'widgets/ticket_dialog.dart';
import 'widgets/ticket_table_header.dart';
import 'widgets/ticket_table_row.dart';

class TicketsScreen extends StatefulWidget {
  const TicketsScreen({super.key, required this.onStatsChanged});

  final VoidCallback onStatsChanged;

  @override
  State<TicketsScreen> createState() => _TicketsScreenState();
}

class _TicketsScreenState extends State<TicketsScreen> {
  List<Ticket> _tickets = [];
  bool _loading = true;
  String? _error;

  String _search = '';
  String? _filterTone;
  String? _filterStatus;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final tickets = await ticketRepository.fetchAll(
        tone: _filterTone, status: _filterStatus, search: _search,
      );
      setState(() => _tickets = tickets);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _openTicket(Ticket ticket) {
    showDialog(
      context: context,
      builder: (_) => TicketDialog(
        ticket: ticket,
        onSaved: () { _load(); widget.onStatsChanged(); },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildFilters(context),
        Expanded(child: _buildBody(context)),
      ],
    );
  }

  Widget _buildFilters(BuildContext context) {
    final colors = context.colors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      color: colors.surface,
      child: Row(
        children: [
          Expanded(
            child: SearchField(
              hint: 'Поиск по ФИО, объекту, номеру прибора...',
              onChanged: (v) { _search = v; _load(); },
            ),
          ),
          const SizedBox(width: 10),
          FilterDropdown(
            hint: 'Тональность',
            items: const ['Негатив', 'Нейтраль', 'Позитив'],
            value: _filterTone,
            onChanged: (v) { setState(() => _filterTone = v); _load(); },
          ),
          const SizedBox(width: 10),
          FilterDropdown(
            hint: 'Статус',
            items: const ['Новое', 'В работе', 'Закрыто'],
            value: _filterStatus,
            onChanged: (v) { setState(() => _filterStatus = v); _load(); },
          ),
          if (_filterTone != null || _filterStatus != null) ...[
            const SizedBox(width: 10),
            TextButton(
              onPressed: () {
                setState(() { _filterTone = null; _filterStatus = null; });
                _load();
              },
              child: Text('Сбросить', style: TextStyle(color: colors.accent, fontSize: 12)),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final colors = context.colors;
    if (_loading) return Center(child: CircularProgressIndicator(color: colors.accent));
    if (_error != null) return Center(child: Text(_error!, style: TextStyle(color: colors.negative)));
    if (_tickets.isEmpty) {
      return Center(child: Text('Нет обращений', style: TextStyle(color: colors.textSecondary)));
    }
    return SingleChildScrollView(
      child: Column(
        children: [
          const TicketTableHeader(),
          ..._tickets.map((t) => TicketTableRow(ticket: t, onTap: () => _openTicket(t))),
        ],
      ),
    );
  }
}
