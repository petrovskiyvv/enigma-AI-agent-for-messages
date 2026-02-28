import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/status_badge.dart';
import '../../domain/ticket.dart';
import '../ticket_colors.dart';

// Мобильное представление тикета — карточка вместо строки таблицы
class TicketCard extends StatelessWidget {
  const TicketCard({super.key, required this.ticket, required this.onTap});

  final Ticket ticket;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final t = ticket;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: colors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    t.fullName.isEmpty ? 'Без имени' : t.fullName,
                    style: TextStyle(color: colors.text, fontWeight: FontWeight.w600, fontSize: 14),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                StatusBadge(text: t.status, color: statusColor(context, t.status)),
              ],
            ),
            if (t.facility.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(t.facility,
                  style: TextStyle(color: colors.textSecondary, fontSize: 12),
                  overflow: TextOverflow.ellipsis),
            ],
            const SizedBox(height: 10),
            if (t.issueSummary.isNotEmpty)
              Text(t.issueSummary,
                  style: TextStyle(color: colors.text, fontSize: 13, height: 1.4),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis),
            const SizedBox(height: 10),
            Row(
              children: [
                StatusBadge(text: t.emotionalTone, color: toneColor(context, t.emotionalTone)),
                const SizedBox(width: 6),
                StatusBadge(text: t.category, color: colors.accent),
                const Spacer(),
                Text(
                  formatDate(t.createdAt).replaceAll('\n', ' '),
                  style: TextStyle(color: colors.textSecondary, fontSize: 11),
                ),
              ],
            ),
            if (t.deviceNumbers.isNotEmpty) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.qr_code, size: 13, color: colors.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(t.deviceNumbers,
                        style: TextStyle(color: colors.textSecondary, fontSize: 12),
                        overflow: TextOverflow.ellipsis),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
