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
    if (_loading) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
    if (_stats == null) return const Center(child: Text('Нет данных', style: TextStyle(color: AppColors.textSecondary)));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _section('Тональность', Map<String, int>.from(_stats!['by_tone'] ?? {}), {
            'Негатив': AppColors.negative,
            'Нейтраль': AppColors.neutral,
            'Позитив': AppColors.positive,
          }),
          const SizedBox(height: 32),
          _section('Категории', Map<String, int>.from(_stats!['by_category'] ?? {}), {}),
          const SizedBox(height: 32),
          _section('Статусы', Map<String, int>.from(_stats!['by_status'] ?? {}), {
            'Новое': AppColors.statusNew,
            'В работе': AppColors.neutral,
            'Закрыто': AppColors.accent,
          }),
        ],
      ),
    );
  }

  Widget _section(String title, Map<String, int> data, Map<String, Color> colorMap) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: AppColors.text, fontSize: 15, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        if (data.isEmpty)
          const Text('Нет данных', style: TextStyle(color: AppColors.textSecondary))
        else
          ...data.entries.map((e) => _bar(e.key, e.value, data.values.fold(0, (a, b) => a > b ? a : b), colorMap[e.key] ?? AppColors.accent)),
      ],
    );
  }

  Widget _bar(String label, int value, int maxValue, Color color) {
    final fraction = maxValue > 0 ? value / maxValue : 0.0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(width: 140, child: Text(label, style: const TextStyle(color: AppColors.text, fontSize: 13))),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: Stack(children: [
                Container(height: 28, color: AppColors.card),
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
