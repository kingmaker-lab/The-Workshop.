/// Progressão 100% local e determinística: não há pontos por repetição.
class AcademyProgress {
  AcademyProgress(Iterable<String> savedIds, Iterable<String> knownIds)
      : completed = savedIds.toSet().intersection(knownIds.toSet());

  final Set<String> completed;

  int get completedCount => completed.length;
  int get xp => completedCount * 100;

  // Cada marco usa quantidade de missões concluídas, não XP editável.
  static const levelThresholds = <int>[0, 3, 8, 15, 25];
  static const levelTitles = <String>[
    'Explorador',
    'Aprendiz',
    'Inventor',
    'Construtor',
    'Mestre da Alcateia',
  ];

  int get level {
    for (var i = levelThresholds.length - 1; i >= 0; i--) {
      if (completedCount >= levelThresholds[i]) return i + 1;
    }
    return 1;
  }

  String get title => levelTitles[level - 1];
  int? get nextLevelAt =>
      level == levelThresholds.length ? null : levelThresholds[level];

  double get levelFraction {
    final next = nextLevelAt;
    if (next == null) return 1;
    final previous = levelThresholds[level - 1];
    return ((completedCount - previous) / (next - previous)).clamp(0.0, 1.0);
  }

  bool hasCompletedPath(String prefix, int required) =>
      completed.where((id) => id.startsWith('$prefix-')).length >= required;

  Map<String, bool> get achievements => {
        'Primeira conquista': completedCount >= 1,
        'Persistente': completedCount >= 5,
        'Investigador': hasCompletedPath('debug', 5),
        'Lógica afiada': hasCompletedPath('logic', 10),
        'Alcateia completa': completedCount >= 25,
      };
}
