import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/status_badge.dart';
import '../../domain/ticket.dart';
import '../ticket_colors.dart';

class TicketTableRow extends StatefulWidget {
  const TicketTableRow({super.key, required this.ticket, required this.onTap});

  final Ticket ticket;
  final VoidCallback onTap;

  @override
  State<TicketTableRow> createState() => _TicketTableRowState();
}

class _TicketTableRowState extends State<TicketTableRow> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final t      = widget.ticket;
    final colors = context.colors;

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit:  (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
          decoration: BoxDecoration(
            color: _hovered ? colors.card : Colors.transparent,
            border: Border(bottom: BorderSide(color: colors.border.withOpacity(0.5))),
          ),
          child: Row(children: [
            _cell(formatDate(t.createdAt), 110, colors, secondary: true),
            _cell(t.fullName.isEmpty       ? '—' : t.fullName,       160, colors),
            _cell(t.facility.isEmpty       ? '—' : t.facility,       160, colors, secondary: true),
            _cell(t.deviceNumbers.isEmpty  ? '—' : t.deviceNumbers,  140, colors, secondary: true),
            _cell(t.deviceType.isEmpty     ? '—' : t.deviceType,     150, colors, secondary: true),
            SizedBox(
              width: 110,
              child: StatusBadge(text: t.emotionalTone, color: toneColor(context, t.emotionalTone)),
            ),
            _cell(t.category.isEmpty ? '—' : t.category, 120, colors),
            Expanded(
              child: Text(
                t.issueSummary.isEmpty ? '—' : t.issueSummary,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: colors.textSecondary, fontSize: 12),
              ),
            ),
            SizedBox(
              width: 100,
              child: StatusBadge(text: t.status, color: statusColor(context, t.status)),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _cell(String text, double width, AppColors colors, {bool secondary = false}) {
    return SizedBox(
      width: width,
      child: Text(
        text,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: secondary ? colors.textSecondary : colors.text,
          fontSize: secondary ? 12 : 13,
        ),
      ),
    );
  }
}
