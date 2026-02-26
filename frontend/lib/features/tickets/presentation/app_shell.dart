import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../analyze/presentation/analyze_screen.dart';
import '../../stats/presentation/stats_screen.dart';
import '../../tickets/data/ticket_repository.dart';
import '../../tickets/presentation/tickets_screen.dart';

const _kBaseUrl = 'http://127.0.0.1:8000';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  static const _tabs = ['Обращения', 'Аналитика', 'Анализ письма'];

  int _tab = 0; // 0=Обращения, 1=Аналитика, 2=Анализ письма
  Map<String, dynamic>? _stats;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final stats = await ticketRepository.fetchStats();
      setState(() => _stats = stats);
    } catch (_) {}
  }

  void _exportCsv() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Откройте в браузере: $_kBaseUrl/api/export/csv'),
        backgroundColor: AppColors.card,
        action: SnackBarAction(label: 'OK', textColor: AppColors.accent, onPressed: () {}),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: Column(
        children: [
          _Header(stats: _stats, onRefresh: _loadStats, onExportCsv: _exportCsv),
          _TabBar(tabs: _tabs, selected: _tab, onSelect: (i) => setState(() => _tab = i)),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildBody() => switch (_tab) {
        0 => TicketsScreen(onStatsChanged: _loadStats),
        1 => const StatsScreen(),
        2 => AnalyzeScreen(onTicketCreated: _loadStats),
        _ => const SizedBox.shrink(),
      };
}

class _Header extends StatelessWidget {
  const _Header({required this.stats, required this.onRefresh, required this.onExportCsv});

  final Map<String, dynamic>? stats;
  final VoidCallback onRefresh;
  final VoidCallback onExportCsv;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          _Logo(),
          const SizedBox(width: 14),
          const Text('Система технической поддержки', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
          const Spacer(),
          if (stats != null) ...[
            _StatBadge(value: '${stats!['total']}', label: 'всего', color: AppColors.text),
            const SizedBox(width: 12),
            _StatBadge(value: '${stats!['by_status']?['Новое'] ?? 0}', label: 'новых', color: AppColors.statusNew),
            const SizedBox(width: 12),
            _StatBadge(value: '${stats!['by_tone']?['Негатив'] ?? 0}', label: 'негатив', color: AppColors.negative),
            const SizedBox(width: 16),
          ],
          _IconBtn(icon: Icons.refresh_rounded, label: 'Обновить', onTap: onRefresh),
          const SizedBox(width: 8),
          _IconBtn(icon: Icons.download_rounded, label: 'CSV', onTap: onExportCsv),
        ],
      ),
    );
  }
}

class _Logo extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.accentDim,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.accent.withOpacity(0.4)),
      ),
      child: const Text('ЭРИС', style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 2)),
    );
  }
}

class _StatBadge extends StatelessWidget {
  const _StatBadge({required this.value, required this.label, required this.color});

  final String value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16)),
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 10)),
      ],
    );
  }
}

class _IconBtn extends StatelessWidget {
  const _IconBtn({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: AppColors.accent, size: 15),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(color: AppColors.text, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}

class _TabBar extends StatelessWidget {
  const _TabBar({required this.tabs, required this.selected, required this.onSelect});

  final List<String> tabs;
  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      child: Row(
        children: List.generate(tabs.length, (i) {
          final active = selected == i;
          return InkWell(
            onTap: () => onSelect(i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 13),
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(color: active ? AppColors.accent : Colors.transparent, width: 2)),
              ),
              child: Text(
                tabs[i],
                style: TextStyle(
                  color: active ? AppColors.accent : AppColors.textSecondary,
                  fontSize: 13,
                  fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
