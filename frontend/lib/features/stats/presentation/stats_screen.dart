import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../tickets/data/ticket_repository.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  Map<String, dynamic>? _stats;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final stats = await ticketRepository.fetchStats();
      setState(() => _stats = stats);
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    if (_loading) return Center(child: CircularProgressIndicator(color: colors.accent));
    if (_stats == null) return Center(child: Text('Нет данных', style: TextStyle(color: colors.textSecondary)));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _section(context, 'Тональность', Map<String, int>.from(_stats!['by_tone'] ?? {}), {
            'Негатив': colors.negative,
            'Нейтраль': colors.neutral,
            'Позитив': colors.positive,
          }),
          const SizedBox(height: 32),
          _section(context, 'Категории', Map<String, int>.from(_stats!['by_category'] ?? {}), {}),
          const SizedBox(height: 32),
          _section(context, 'Статусы', Map<String, int>.from(_stats!['by_status'] ?? {}), {
            'Новое':    colors.statusNew,
            'В работе': colors.neutral,
            'Закрыто':  colors.accent,
          }),
        ],
      ),
    );
  }

  Widget _section(BuildContext context, String title, Map<String, int> data, Map<String, Color> colorMap) {
    final colors = context.colors;
    final maxVal = data.values.fold(0, (a, b) => a > b ? a : b);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: TextStyle(color: colors.text, fontSize: 15, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        if (data.isEmpty)
          Text('Нет данных', style: TextStyle(color: colors.textSecondary))
        else
          ...data.entries.map((e) => _bar(context, e.key, e.value, maxVal, colorMap[e.key] ?? colors.accent)),
      ],
    );
  }

  Widget _bar(BuildContext context, String label, int value, int maxValue, Color color) {
    final colors  = context.colors;
    final fraction = maxValue > 0 ? value / maxValue : 0.0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(width: 140, child: Text(label, style: TextStyle(color: colors.text, fontSize: 13))),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: Stack(children: [
                Container(height: 28, color: colors.card),
                FractionallySizedBox(
                  widthFactor: fraction,
                  child: Container(height: 28, color: color.withOpacity(0.7)),
                ),
              ]),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 30,
            child: Text('$value', style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
