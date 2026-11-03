import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const WolfpackAcademyApp());
}

class WolfpackAcademyApp extends StatelessWidget {
  const WolfpackAcademyApp({super.key});

  static const background = Color(0xFF0A1020);
  static const card = Color(0xFF17213A);
  static const accent = Color(0xFF45D6FF);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Wolfpack Academy',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: background,
        colorScheme: ColorScheme.fromSeed(
          seedColor: accent,
          brightness: Brightness.dark,
          surface: card,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: background,
          foregroundColor: Colors.white,
          centerTitle: false,
        ),
        cardTheme: const CardThemeData(
          color: card,
          elevation: 0,
          margin: EdgeInsets.zero,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            foregroundColor: background,
            backgroundColor: accent,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          ),
        ),
      ),
      home: const AcademyHome(),
    );
  }
}

class StudyPath {
  final String id;
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  const StudyPath(this.id, this.title, this.subtitle, this.icon, this.color);
}

const paths = <StudyPath>[
  StudyPath(
    'logic',
    'Lógica de programação',
    'Descubra como o código pensa.',
    Icons.account_tree_outlined,
    Color(0xFF48D6F8),
  ),
  StudyPath(
    'debug',
    'Caça aos bugs',
    'Encontre, explique e corrija falhas.',
    Icons.bug_report_outlined,
    Color(0xFFFFB673),
  ),
];

class Mission {
  final String id;
  final String pathId;
  final String title;
  final String language;
  final String question;
  final List<String> choices;
  final int correctIndex;
  final String explanation;

  const Mission({
    required this.id,
    required this.pathId,
    required this.title,
    required this.language,
    required this.question,
    required this.choices,
    required this.correctIndex,
    required this.explanation,
  });
}

// Conteudo inicial embutido para funcionar sem internet e sem conta.
// Futuramente pode ser substituido por conteudo versionado da API.
const missions = <Mission>[
  Mission(
    id: 'logic-001',
    pathId: 'logic',
    title: 'Booleanos',
    language: 'Python',
    question: 'O que print(3 > 2) mostra?',
    choices: ['True', 'False', '3'],
    correctIndex: 0,
    explanation: 'O operador > compara dois valores. Como 3 é maior que 2, o resultado é True.',
  ),
  Mission(
    id: 'logic-002',
    pathId: 'logic',
    title: 'Índices',
    language: 'Python',
    question: "Se itens = ['a', 'b', 'c'], qual é o valor de itens[1]?",
    choices: ["'a'", "'b'", "'c'"],
    correctIndex: 1,
    explanation: "Em Python, listas começam no índice zero: itens[0] é 'a' e itens[1] é 'b'.",
  ),
  Mission(
    id: 'logic-003',
    pathId: 'logic',
    title: 'Repetição',
    language: 'Python',
    question: 'Quantas vezes o corpo de for i in range(3): executa?',
    choices: ['2 vezes', '3 vezes', '4 vezes'],
    correctIndex: 1,
    explanation: 'range(3) gera 0, 1 e 2. Portanto são três iterações.',
  ),
  Mission(
    id: 'debug-001',
    pathId: 'debug',
    title: 'Atribuição ≠ comparação',
    language: 'JavaScript',
    question: 'Qual é o problema em if (age = 18) ?',
    choices: [
      'Deveria usar === em vez de =',
      'Não pode usar parênteses',
      '18 sempre deve ser uma string'
    ],
    correctIndex: 0,
    explanation: '= atribui um valor. === compara valor e tipo. Em uma condição, isso faz diferença.',
  ),
  Mission(
    id: 'debug-002',
    pathId: 'debug',
    title: 'Fora dos limites',
    language: 'Python',
    question: 'O que ocorre em nums = [10, 20]; nums[2]?',
    choices: ['Retorna 20', 'Retorna None', 'Lança IndexError'],
    correctIndex: 2,
    explanation: 'A lista tem posições 0 e 1. A posição 2 não existe e gera IndexError.',
  ),
];

class AcademyHome extends StatefulWidget {
  const AcademyHome({super.key});

  @override
  State<AcademyHome> createState() => _AcademyHomeState();
}

class _AcademyHomeState extends State<AcademyHome> {
  static const progressKey = 'completed_missions_v1';
  Set<String> _completed = <String>{};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _restoreProgress();
  }

  Future<void> _restoreProgress() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!mounted) return;
      setState(() {
        _completed = (prefs.getStringList(progressKey) ?? <String>[]).toSet();
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Future<void> _markComplete(String id) async {
    if (!missions.any((mission) => mission.id == id)) return;
    if (!_completed.add(id)) return;
    setState(() {});
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList(progressKey, _completed.toList()..sort());
    } catch (_) {
      // O jogo continua acessivel mesmo se persistencia local falhar.
    }
  }

  @override
  Widget build(BuildContext context) {
    final completedCount = _completed.length;
    final missionCount = missions.length;
    final fraction = missionCount == 0 ? 0.0 : completedCount / missionCount;

    return Scaffold(
      appBar: AppBar(
        title: const Text('WOLFPACK  /  ACADEMY',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, letterSpacing: 1.3)),
        actions: [
          IconButton(
            tooltip: 'Sobre o projeto',
            icon: const Icon(Icons.info_outline),
            onPressed: () => showAboutDialog(
              context: context,
              applicationName: 'Wolfpack Academy',
              applicationVersion: '0.1.0',
              children: [
                const Text('Uma iniciativa educacional gratuita da The Workshop. '
                    'Este protótipo funciona offline e não exige conta.'),
              ],
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 32),
                children: [
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(24),
                      gradient: const LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [Color(0xFF173A57), Color(0xFF17213A)],
                      ),
                      border: Border.all(color: const Color(0x5545D6FF)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('BUILD. BREAK. LEARN.',
                          style: TextStyle(color: WolfpackAcademyApp.accent,
                            fontWeight: FontWeight.w800, letterSpacing: 2)),
                        const SizedBox(height: 12),
                        const Text('Sua jornada começa aqui.',
                          style: TextStyle(fontSize: 29, height: 1.15,
                            fontWeight: FontWeight.w800)),
                        const SizedBox(height: 10),
                        const Text('Aprenda programação experimentando, '
                            'errando e entendendo o porquê.',
                          style: TextStyle(color: Color(0xFFD0DAE9), height: 1.4)),
                        const SizedBox(height: 24),
                        Row(
                          children: [
                            const Icon(Icons.bolt, size: 20,
                              color: WolfpackAcademyApp.accent),
                            const SizedBox(width: 6),
                            Text((completedCount * 100).toString() + ' XP',
                              style: const TextStyle(fontSize: 19,
                                fontWeight: FontWeight.bold)),
                            const Spacer(),
                            Text('$completedCount / $missionCount missões',
                              style: const TextStyle(color: Color(0xFFC1CEDC))),
                          ],
                        ),
                        const SizedBox(height: 12),
                        LinearProgressIndicator(
                          value: fraction,
                          minHeight: 9,
                          borderRadius: BorderRadius.circular(10),
                          backgroundColor: const Color(0xFF2B3D55),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 30),
                  const Text('Escolha sua trilha',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  const Text('Todas as missões funcionam offline.',
                    style: TextStyle(color: Color(0xFFAAB9CF))),
                  const SizedBox(height: 18),
                  for (final path in paths) ...[
                    _PathCard(
                      path: path,
                      completed: _completed,
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => PathScreen(
                            path: path,
                            completed: _completed,
                            onComplete: _markComplete,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],
                  const SizedBox(height: 10),
                  const Text(
                    'SEM ANÚNCIOS  •  SEM CADASTRO  •  100% GRATUITO',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 10, letterSpacing: 1.2,
                      color: Color(0xFF9BB1C9)),
                  ),
                ],
              ),
            ),
    );
  }
}

class _PathCard extends StatelessWidget {
  const _PathCard({
    required this.path,
    required this.completed,
    required this.onTap,
  });

  final StudyPath path;
  final Set<String> completed;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final available = missions.where((m) => m.pathId == path.id).toList();
    final done = available.where((m) => completed.contains(m.id)).length;
    return Card(
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFF32415C)),
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: path.color.withValues(alpha: 0.13),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(path.icon, color: path.color, size: 30),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(path.title,
                      style: const TextStyle(fontSize: 17,
                        fontWeight: FontWeight.bold)),
                    const SizedBox(height: 5),
                    Text(path.subtitle,
                      style: const TextStyle(color: Color(0xFFB1BDD0))),
                    const SizedBox(height: 8),
                    Text('$done / ${available.length} concluídas',
                      style: TextStyle(color: path.color, fontSize: 12)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Color(0xFFB1BDD0)),
            ],
          ),
        ),
      ),
    );
  }
}

class PathScreen extends StatefulWidget {
  const PathScreen({
    super.key,
    required this.path,
    required this.completed,
    required this.onComplete,
  });
  final StudyPath path;
  final Set<String> completed;
  final Future<void> Function(String) onComplete;

  @override
  State<PathScreen> createState() => _PathScreenState();
}

class _PathScreenState extends State<PathScreen> {
  @override
  Widget build(BuildContext context) {
    final available = missions.where((m) => m.pathId == widget.path.id).toList();
    return Scaffold(
      appBar: AppBar(title: Text(widget.path.title)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(widget.path.subtitle,
            style: const TextStyle(fontSize: 18, color: Color(0xFFB1BDD0))),
          const SizedBox(height: 20),
          for (var i = 0; i < available.length; i++)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 18, vertical: 12),
                  leading: CircleAvatar(
                    backgroundColor: const Color(0xFF293752),
                    child: widget.completed.contains(available[i].id)
                        ? const Icon(Icons.check_circle, color: Color(0xFF6DE7B4))
                        : Text((i + 1).toString()),
                  ),
                  title: Text(available[i].title,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(available[i].language + ' • Desafio interativo'),
                  trailing: const Icon(Icons.play_arrow_rounded),
                  onTap: () async {
                    await Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => MissionScreen(
                          mission: available[i],
                          onComplete: widget.onComplete,
                        ),
                      ),
                    );
                    if (mounted) setState(() {});
                  },
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class MissionScreen extends StatefulWidget {
  const MissionScreen({
    super.key,
    required this.mission,
    required this.onComplete,
  });
  final Mission mission;
  final Future<void> Function(String) onComplete;

  @override
  State<MissionScreen> createState() => _MissionScreenState();
}

class _MissionScreenState extends State<MissionScreen> {
  int? _selected;

  @override
  Widget build(BuildContext context) {
    final mission = widget.mission;
    final submitted = _selected != null;
    final correct = _selected == mission.correctIndex;
    return Scaffold(
      appBar: AppBar(title: Text(mission.language + ' • Missão')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Text('RESOLVA O DESAFIO',
              style: TextStyle(color: WolfpackAcademyApp.accent,
                letterSpacing: 1.8, fontWeight: FontWeight.w800)),
            const SizedBox(height: 10),
            Text(mission.title,
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: WolfpackAcademyApp.card,
                borderRadius: BorderRadius.circular(20),
              ),
              child: SelectableText(mission.question,
                style: const TextStyle(fontSize: 20, height: 1.5)),
            ),
            const SizedBox(height: 24),
            for (var i = 0; i < mission.choices.length; i++) ...[
              OutlinedButton(
                onPressed: submitted ? null : () {
                  setState(() => _selected = i);
                  if (i == mission.correctIndex) {
                    widget.onComplete(mission.id);
                  }
                },
                style: OutlinedButton.styleFrom(
                  alignment: Alignment.centerLeft,
                  padding: const EdgeInsets.all(18),
                  foregroundColor: Colors.white,
                  disabledForegroundColor: Colors.white,
                  side: BorderSide(
                    color: submitted && i == mission.correctIndex
                        ? const Color(0xFF6DE7B4)
                        : submitted && _selected == i
                            ? const Color(0xFFFF8585)
                            : const Color(0xFF42526A),
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
                ),
                child: Text(mission.choices[i],
                  style: const TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 12),
            ],
            if (submitted) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: correct ? const Color(0xFF163F39) : const Color(0xFF423128),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(correct ? '✓ Resposta correta! +100 XP'
                        : 'Vamos entender o erro.',
                      style: const TextStyle(fontSize: 18,
                        fontWeight: FontWeight.bold)),
                    const SizedBox(height: 10),
                    Text(mission.explanation,
                      style: const TextStyle(height: 1.5)),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Voltar às missões'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
