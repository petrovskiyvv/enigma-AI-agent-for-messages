import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class TicketTableHeader extends StatelessWidget {
  const TicketTableHeader({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final mobile = MediaQuery.of(context).size.width < 900;

    if (mobile) return const SizedBox.shrink();

    return Container(
      color: colors.card,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          _h('Дата',        2, colors),
          _h('ФИО',         3, colors),
          _h('Объект',      3, colors),
          _h('Приборы',     2, colors),
          _h('Тип прибора', 2, colors),
          _h('Тональность', 2, colors),
          _h('Категория',   2, colors),
          _h('Суть',        4, colors),
          _h('Статус',      2, colors),
        ],
      ),
    );
  }

  Widget _h(String label, int flex, AppColors colors) => Expanded(
    flex: flex,
    child: Text(
      label,
      style: TextStyle(
        color: colors.textSecondary,
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      ),
    ),
  );
}