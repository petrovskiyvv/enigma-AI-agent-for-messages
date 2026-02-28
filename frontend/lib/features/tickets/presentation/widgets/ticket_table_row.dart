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
    final width  = MediaQuery.of(context).size.width;
    final mobile = width < 900;

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
          child: mobile
              ? _buildMobileCard(t, colors)
              : _buildDesktopRow(t, colors),
        ),
      ),
    );
  }

  Widget _buildDesktopRow(Ticket t, AppColors colors) {
    return Row(children: [
      _flex(formatDate(t.createdAt),               2, colors, secondary: true),
      _flex(t.fullName.isEmpty      ? '—' : t.fullName,      3, colors),
      _flex(t.facility.isEmpty      ? '—' : t.facility,      3, colors, secondary: true),
      _flex(t.deviceNumbers.isEmpty ? '—' : t.deviceNumbers, 2, colors, secondary: true),
      _flex(t.deviceType.isEmpty    ? '—' : t.deviceType,    2, colors, secondary: true),
      Expanded(
        flex: 2,
        child: StatusBadge(
          text: t.emotionalTone,
          color: toneColor(context, t.emotionalTone),
        ),
      ),
      _flex(t.category.isEmpty ? '—' : t.category, 2, colors),
      _flex(t.issueSummary.isEmpty ? '—' : t.issueSummary, 4, colors, secondary: true),
      Expanded(
        flex: 2,
        child: StatusBadge(text: t.status, color: statusColor(context, t.status)),
      ),
    ]);
  }

  Widget _buildMobileCard(Ticket t, AppColors colors) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                t.fullName.isEmpty ? '—' : t.fullName,
                style: TextStyle(
                  color: colors.text,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            StatusBadge(text: t.status, color: statusColor(context, t.status)),
          ],
        ),
        const SizedBox(height: 4),
        if (t.facility.isNotEmpty)
          Text(
            t.facility,
            style: TextStyle(color: colors.textSecondary, fontSize: 12),
            overflow: TextOverflow.ellipsis,
          ),
        const SizedBox(height: 4),
        Row(
          children: [
            StatusBadge(
              text: t.emotionalTone,
              color: toneColor(context, t.emotionalTone),
            ),
            const SizedBox(width: 8),
            if (t.category.isNotEmpty)
              Text(
                t.category,
                style: TextStyle(color: colors.textSecondary, fontSize: 11),
              ),
            const Spacer(),
            Text(
              formatDate(t.createdAt),
              style: TextStyle(color: colors.textSecondary, fontSize: 11),
            ),
          ],
        ),
        if (t.issueSummary.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            t.issueSummary,
            style: TextStyle(color: colors.textSecondary, fontSize: 12),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ],
    );
  }

  Widget _flex(String text, int flex, AppColors colors, {bool secondary = false}) {
    return Expanded(
      flex: flex,
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