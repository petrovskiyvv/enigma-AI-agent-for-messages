import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/responsive.dart';
import '../../analyze/presentation/analyze_screen.dart';
import '../../stats/presentation/stats_screen.dart';
import '../../tickets/data/ticket_repository.dart';
import '../../tickets/presentation/tickets_screen.dart';
import '../../../main.dart';

const _kBaseUrl = 'http://127.0.0.1:8000';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
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
        backgroundColor: context.colors.card,
        action: SnackBarAction(label: 'OK', textColor: context.colors.accent, onPressed: () {}),
      ),
    );
  }

  Widget _buildBody() => switch (_tab) {
        0 => TicketsScreen(onStatsChanged: _loadStats),
        1 => const StatsScreen(),
        2 => AnalyzeScreen(onTicketCreated: _loadStats),
        _ => const SizedBox.shrink(),
      };

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final mobile = isMobile(context);

    return Scaffold(
      backgroundColor: colors.bg,
      bottomNavigationBar: mobile
          ? _MobileNavBar(selected: _tab, onSelect: (i) => setState(() => _tab = i))
          : null,
      body: Column(
        children: [
          mobile
              ? _MobileHeader(stats: _stats, onRefresh: _loadStats, onExportCsv: _exportCsv)
              : _DesktopHeader(stats: _stats, onRefresh: _loadStats, onExportCsv: _exportCsv),
          if (!mobile)
            _DesktopTabBar(
              selected: _tab,
              onSelect: (i) => setState(() => _tab = i),
            ),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }
}

// ─── Десктопная шапка ────────────────────────────────────────────────────────

class _DesktopHeader extends StatelessWidget {
  const _DesktopHeader({required this.stats, required this.onRefresh, required this.onExportCsv});

  final Map<String, dynamic>? stats;
  final VoidCallback onRefresh;
  final VoidCallback onExportCsv;

  @override
  Widget build(BuildContext context) {
    final colors   = context.colors;
    final appState = EnigmaApp.of(context);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(bottom: BorderSide(color: colors.border)),
      ),
      child: Row(
        children: [
          _Logo(),
          const SizedBox(width: 14),
          Text('Система технической поддержки',
              style: TextStyle(color: colors.textSecondary, fontSize: 13)),
          const Spacer(),
          if (stats != null) ...[
            _StatBadge(value: '${stats!['total']}',                     label: 'всего',   color: colors.text),
            const SizedBox(width: 12),
            _StatBadge(value: '${stats!['by_status']?['Новое'] ?? 0}', label: 'новых',   color: colors.statusNew),
            const SizedBox(width: 12),
            _StatBadge(value: '${stats!['by_tone']?['Негатив'] ?? 0}', label: 'негатив', color: colors.negative),
            const SizedBox(width: 16),
          ],
          _IconBtn(icon: Icons.refresh_rounded,  label: 'Обновить', onTap: onRefresh),
          const SizedBox(width: 8),
          _IconBtn(icon: Icons.download_rounded, label: 'CSV',      onTap: onExportCsv),
          const SizedBox(width: 8),
          _IconBtn(
            icon:  appState.isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
            label: appState.isDark ? 'Светлая' : 'Тёмная',
            onTap: appState.toggleTheme,
          ),
        ],
      ),
    );
  }
}

// ─── Мобильная шапка ─────────────────────────────────────────────────────────

class _MobileHeader extends StatelessWidget {
  const _MobileHeader({required this.stats, required this.onRefresh, required this.onExportCsv});

  final Map<String, dynamic>? stats;
  final VoidCallback onRefresh;
  final VoidCallback onExportCsv;

  @override
  Widget build(BuildContext context) {
    final colors   = context.colors;
    final appState = EnigmaApp.of(context);

    return Container(
      padding: EdgeInsets.only(
        left: 16, right: 8,
        top: MediaQuery.of(context).padding.top + 8,
        bottom: 8,
      ),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(bottom: BorderSide(color: colors.border)),
      ),
      child: Row(
        children: [
          _Logo(),
          const SizedBox(width: 10),
          if (stats != null) ...[
            _StatBadge(value: '${stats!['total']}',                     label: 'всего',   color: colors.text),
            const SizedBox(width: 10),
            _StatBadge(value: '${stats!['by_status']?['Новое'] ?? 0}', label: 'новых',   color: colors.statusNew),
            const SizedBox(width: 10),
            _StatBadge(value: '${stats!['by_tone']?['Негатив'] ?? 0}', label: 'негатив', color: colors.negative),
          ],
          const Spacer(),
          IconButton(
            onPressed: onRefresh,
            icon: Icon(Icons.refresh_rounded, color: colors.accent, size: 20),
            tooltip: 'Обновить',
          ),
          IconButton(
            onPressed: onExportCsv,
            icon: Icon(Icons.download_rounded, color: colors.accent, size: 20),
            tooltip: 'CSV',
          ),
          IconButton(
            onPressed: appState.toggleTheme,
            icon: Icon(
              appState.isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
              color: colors.accent,
              size: 20,
            ),
            tooltip: appState.isDark ? 'Светлая тема' : 'Тёмная тема',
          ),
        ],
      ),
    );
  }
}

// ─── Десктопный таб-бар ───────────────────────────────────────────────────────

class _DesktopTabBar extends StatelessWidget {
  const _DesktopTabBar({required this.selected, required this.onSelect});

  final int selected;
  final ValueChanged<int> onSelect;

  static const _tabs = ['Обращения', 'Аналитика', 'Анализ письма'];

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      color: colors.surface,
      child: Row(
        children: List.generate(_tabs.length, (i) {
          final active = selected == i;
          return InkWell(
            onTap: () => onSelect(i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 13),
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(
                  color: active ? colors.accent : Colors.transparent,
                  width: 2,
                )),
              ),
              child: Text(
                _tabs[i],
                style: TextStyle(
                  color:      active ? colors.accent : colors.textSecondary,
                  fontSize:   13,
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

// ─── Мобильный bottom nav ─────────────────────────────────────────────────────

class _MobileNavBar extends StatelessWidget {
  const _MobileNavBar({required this.selected, required this.onSelect});

  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(top: BorderSide(color: colors.border)),
      ),
      child: NavigationBar(
        backgroundColor: colors.surface,
        indicatorColor: colors.accentDim,
        selectedIndex: selected,
        onDestinationSelected: onSelect,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        destinations: [
          NavigationDestination(
            icon:         Icon(Icons.inbox_outlined,        color: colors.textSecondary),
            selectedIcon: Icon(Icons.inbox,                 color: colors.accent),
            label: 'Обращения',
          ),
          NavigationDestination(
            icon:         Icon(Icons.bar_chart_outlined,    color: colors.textSecondary),
            selectedIcon: Icon(Icons.bar_chart,             color: colors.accent),
            label: 'Аналитика',
          ),
          NavigationDestination(
            icon:         Icon(Icons.auto_awesome_outlined, color: colors.textSecondary),
            selectedIcon: Icon(Icons.auto_awesome,          color: colors.accent),
            label: 'Анализ',
          ),
        ],
      ),
    );
  }
}

// ─── Общие виджеты шапки ─────────────────────────────────────────────────────

class _Logo extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: colors.accentDim,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: colors.accent.withOpacity(0.4)),
      ),
      child: Text('ЭРИС',
          style: TextStyle(color: colors.accent, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 2)),
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
    final colors = context.colors;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 16)),
        Text(label, style: TextStyle(color: colors.textSecondary, fontSize: 10)),
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
    final colors = context.colors;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: colors.card,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: colors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: colors.accent, size: 15),
            const SizedBox(width: 6),
            Text(label, style: TextStyle(color: colors.text, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
