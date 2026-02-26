import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class TicketTableHeader extends StatelessWidget {
  const TicketTableHeader({super.key});

  static const _columns = [
    ('Дата', 110.0),
    ('ФИО', 160.0),
    ('Объект', 160.0),
    ('Приборы', 140.0),
    ('Тип прибора', 150.0),
    ('Тональность', 110.0),
    ('Категория', 120.0),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.card,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          ..._columns.map(
            (col) => SizedBox(
              width: col.$2,
              child: _headerText(col.$1),
            ),
          ),
          Expanded(child: _headerText('Суть')),
          SizedBox(width: 100, child: _headerText('Статус')),
        ],
      ),
    );
  }

  Widget _headerText(String label) => Text(
        label,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      );
}
