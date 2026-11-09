import 'package:flutter_test/flutter_test.dart';
import 'package:wolfpack_academy/main.dart';
import 'package:wolfpack_academy/progression.dart';

void main() {
  test('Catalogo tem 25 missões únicas divididas em 3 trilhas', () {
    expect(missions.length, 25);
    expect(missions.map((m) => m.id).toSet().length, 25);
    expect(missions.where((m) => m.pathId == 'logic').length, 10);
    expect(missions.where((m) => m.pathId == 'debug').length, 10);
    expect(missions.where((m) => m.pathId == 'web').length, 5);
    for (final m in missions) {
      expect(m.choices.length, greaterThanOrEqualTo(3));
      expect(m.correctIndex, inInclusiveRange(0, m.choices.length - 1));
      expect(m.explanation.trim(), isNotEmpty);
      expect(missions.where((other) => other.id == m.id).length, 1);
    }
  });

  test('XP contabiliza IDs únicos conhecidos, ignorando dados inválidos', () {
    final progress = AcademyProgress(
      ['logic-001', 'logic-001', 'id-desconhecido'],
      missions.map((m) => m.id),
    );
    expect(progress.xp, 100);
    expect(progress.completedCount, 1);
    expect(progress.level, 1);
    expect(progress.achievements['Primeira conquista'], isTrue);
  });

  test('Marcos dos 5 níveis são determinísticos', () {
    final ids = missions.map((m) => m.id).toList();
    final expected = <int, int>{0: 1, 2: 1, 3: 2, 7: 2, 8: 3, 14: 3,
      15: 4, 24: 4, 25: 5};
    for (final item in expected.entries) {
      final progress = AcademyProgress(ids.take(item.key), ids);
      expect(progress.level, item.value);
    }
    final complete = AcademyProgress(ids, ids);
    expect(complete.xp, 2500);
    expect(complete.levelFraction, 1);
    expect(complete.nextLevelAt, isNull);
    expect(complete.achievements.values.every((v) => v), isTrue);
  });

  test('Progresso legado permanece válido com as novas missões', () {
    final legacySavedIds = ['logic-001', 'debug-001'];
    final progress = AcademyProgress(
      legacySavedIds,
      missions.map((m) => m.id),
    );
    expect(progress.xp, 200);
    expect(progress.completed.containsAll(legacySavedIds), isTrue);
    expect(progress.achievements['Primeira conquista'], isTrue);
  });
}
