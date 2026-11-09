import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:wolfpack_academy/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('Mostra trilhas e progresso inicial', (tester) async {
    await tester.pumpWidget(const WolfpackAcademyApp());
    await tester.pumpAndSettle();

    expect(find.text('Sua jornada começa aqui.'), findsOneWidget);
    expect(find.text('Nível 1 • Explorador'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Lógica de programação'), 250,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Lógica de programação'), findsOneWidget);
    expect(find.text('Conquistas'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Caça aos bugs'), 250,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Caça aos bugs'), findsOneWidget);
    expect(find.text('0 XP'), findsOneWidget);
  });

  testWidgets('Abre missão e explica a resposta correta', (tester) async {
    await tester.pumpWidget(const WolfpackAcademyApp());
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Lógica de programação'), 250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Lógica de programação'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Booleanos'));
    await tester.pumpAndSettle();

    expect(find.text('O que print(3 > 2) mostra?'), findsOneWidget);
    await tester.tap(find.text('True'));
    await tester.pumpAndSettle();

    expect(find.text('✓ Resposta correta!'), findsOneWidget);
    expect(find.textContaining('O operador > compara'), findsOneWidget);
  });
  testWidgets('Explica erro, permite tentar novamente e soma XP uma vez', (tester) async {
    await tester.pumpWidget(const WolfpackAcademyApp());
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Lógica de programação'), 250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Lógica de programação'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Booleanos'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('False'));
    await tester.pumpAndSettle();
    expect(find.text('Vamos entender o erro.'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('Tentar novamente'), 230,
      scrollable: find.byType(Scrollable).last,
    );
    await tester.tap(find.text('Tentar novamente'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('True'));
    await tester.pumpAndSettle();
    expect(find.text('✓ Resposta correta!'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('Voltar às missões'), 230,
      scrollable: find.byType(Scrollable).last,
    );
    await tester.tap(find.text('Voltar às missões'));
    await tester.pumpAndSettle();
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('100 XP'), findsOneWidget);
  });

}
