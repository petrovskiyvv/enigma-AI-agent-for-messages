import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/responsive.dart';
import '../../../core/widgets/filter_dropdown.dart';
import '../../../core/widgets/search_field.dart';
import '../data/ticket_repository.dart';
import '../domain/ticket.dart';
import 'widgets/ticket_card.dart';
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
    final mobile = isMobile(context);

    final searchField = SearchField(
      hint: 'Поиск по ФИО, объекту, номеру прибора...',
      onChanged: (v) { _search = v; _load(); },
    );
    final toneDropdown = FilterDropdown(
      hint: 'Тональность',
      items: const ['Негатив', 'Нейтраль', 'Позитив'],
      value: _filterTone,
      onChanged: (v) { setState(() => _filterTone = v); _load(); },
    );
    final statusDropdown = FilterDropdown(
      hint: 'Статус',
      items: const ['Новое', 'В работе', 'Отправлено', 'Закрыто'],
      value: _filterStatus,
      onChanged: (v) { setState(() => _filterStatus = v); _load(); },
    );
    final resetBtn = (_filterTone != null || _filterStatus != null)
        ? TextButton(
      onPressed: () {
        setState(() { _filterTone = null; _filterStatus = null; });
        _load();
      },
      child: Text('Сбросить', style: TextStyle(color: colors.accent, fontSize: 12)),
    )
        : null;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: mobile ? 12 : 20, vertical: 10),
      color: colors.surface,
      child: mobile
          ? Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          searchField,
          const SizedBox(height: 8),
          Row(children: [
            toneDropdown,
            const SizedBox(width: 8),
            statusDropdown,
            if (resetBtn != null) ...[const SizedBox(width: 4), resetBtn],
          ]),
        ],
      )
          : Row(children: [
        Expanded(child: searchField),
        const SizedBox(width: 10),
        toneDropdown,
        const SizedBox(width: 10),
        statusDropdown,
        if (resetBtn != null) ...[const SizedBox(width: 10), resetBtn],
      ]),
    );
  }

  Widget _buildBody(BuildContext context) {
    final colors = context.colors;
    final mobile = isMobile(context);

    if (_loading) return Center(child: CircularProgressIndicator(color: colors.accent));
    if (_error != null) return Center(child: Text(_error!, style: TextStyle(color: colors.negative)));
    if (_tickets.isEmpty) {
      return Center(child: Text('Нет обращений', style: TextStyle(color: colors.textSecondary)));
    }

    if (mobile) {
      return ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _tickets.length,
        itemBuilder: (_, i) => TicketCard(
          ticket: _tickets[i],
          onTap: () => _openTicket(_tickets[i]),
        ),
      );
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