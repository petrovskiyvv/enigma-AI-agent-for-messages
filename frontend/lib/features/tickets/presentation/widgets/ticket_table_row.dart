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
    final t = widget.ticket;
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
          decoration: BoxDecoration(
            color: _hovered ? AppColors.card : Colors.transparent,
            border: Border(bottom: BorderSide(color: AppColors.border.withOpacity(0.5))),
          ),
          child: Row(children: [
            _cell(formatDate(t.createdAt), 110, secondary: true),
            _cell(t.fullName.isEmpty ? '—' : t.fullName, 160),
            _cell(t.facility.isEmpty ? '—' : t.facility, 160, secondary: true),
            _cell(t.deviceNumbers.isEmpty ? '—' : t.deviceNumbers, 140, secondary: true),
            _cell(t.deviceType.isEmpty ? '—' : t.deviceType, 150, secondary: true),
            SizedBox(
              width: 110,
              child: StatusBadge(text: t.emotionalTone, color: toneColor(t.emotionalTone)),
            ),
            _cell(t.category.isEmpty ? '—' : t.category, 120),
            Expanded(
              child: Text(
                t.issueSummary.isEmpty ? '—' : t.issueSummary,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ),
            SizedBox(
              width: 100,
              child: StatusBadge(text: t.status, color: statusColor(t.status)),
            ),
          ]),
        ),
      ),
    );
  }

  Widget _cell(String text, double width, {bool secondary = false}) {
    return SizedBox(
      width: width,
      child: Text(
        text,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: secondary ? AppColors.textSecondary : AppColors.text,
          fontSize: secondary ? 12 : 13,
        ),
      ),
    );
  }
}