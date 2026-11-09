import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'progression.dart';

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
  StudyPath(
    'web',
    'Fundamentos da web',
    'HTML, CSS e JavaScript para começar.',
    Icons.language_outlined,
    Color(0xFF9A96FF),
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
    question: 'O que ocorre em nums = [10, 20  Mission(
    id: "logic-004",
    pathId: "logic",
    title: "Variáveis",
    language: "Python",
    question: "Depois de x = 5 e x = x + 2, quanto vale x?",
    choices: ["5", "7", "2"],
    correctIndex: 1,
    explanation: "A segunda atribuição usa o valor anterior (5) e soma 2, resultando em 7.",
  ),
  Mission(
    id: "logic-005",
    pathId: "logic",
    title: "Operadores",
    language: "Python",
    question: "Quanto vale 7 // 2 em Python?",
    choices: ["3", "3.5", "1"],
    correctIndex: 0,
    explanation: "O operador // realiza divisão inteira por piso. Para números positivos, 7 // 2 vale 3.",
  ),
  Mission(
    id: "logic-006",
    pathId: "logic",
    title: "Condições",
    language: "Python",
    question: "Com idade = 17, o teste idade >= 18 retorna o quê?",
    choices: ["True", "False", "18"],
    correctIndex: 1,
    explanation: "17 não é maior nem igual a 18, portanto a expressão booleana retorna False.",
  ),
  Mission(
    id: "logic-007",
    pathId: "logic",
    title: "Listas",
    language: "Python",
    question: "Qual é o tamanho de [2, 4, 6, 8]?",
    choices: ["3", "4", "8"],
    correctIndex: 1,
    explanation: "Há quatro elementos na lista. A função len retorna a quantidade de elementos.",
  ),
  Mission(
    id: "logic-008",
    pathId: "logic",
    title: "Funções",
    language: "Python",
    question: "Uma função que executa return 2 * 3 devolve:",
    choices: ["6", "5", "None"],
    correctIndex: 0,
    explanation: "A expressão 2 * 3 é avaliada antes do return; o valor devolvido é 6.",
  ),
  Mission(
    id: "logic-009",
    pathId: "logic",
    title: "Strings",
    language: "Python",
    question: "Qual é o resultado de 'lobo'.upper()?",
    choices: ["'Lobo'", "'LOBO'", "'lobo'"],
    correctIndex: 1,
    explanation: "O método upper transforma todas as letras do texto em maiúsculas.",
  ),
  Mission(
    id: "logic-010",
    pathId: "logic",
    title: "Booleanos compostos",
    language: "Python",
    question: "Quanto vale True and False?",
    choices: ["True", "False", "None"],
    correctIndex: 1,
    explanation: "O operador and só resulta em True quando as duas condições são verdadeiras.",
  ),
  Mission(
    id: "debug-003",
    pathId: "debug",
    title: "Indentação",
    language: "Python",
    question: "O que está errado em if True: seguido de print('ok') sem recuo?",
    choices: ["Falta indentação no bloco", "O texto precisa ser número", "if não existe em Python"],
    correctIndex: 0,
    explanation: "Python usa indentação para delimitar blocos; o print precisa estar recuado.",
  ),
  Mission(
    id: "debug-004",
    pathId: "debug",
    title: "Nome inexistente",
    language: "Python",
    question: "O que acontece se executarmos print(total) sem definir total?",
    choices: ["Imprime zero", "Gera NameError", "Retorna False"],
    correctIndex: 1,
    explanation: "Uma variável não definida provoca NameError quando é acessada.",
  ),
  Mission(
    id: "debug-005",
    pathId: "debug",
    title: "Tipo incompatível",
    language: "Python",
    question: "O que ocorre com '3' + 2 em Python?",
    choices: ["Retorna 5", "Retorna '32'", "Gera TypeError"],
    correctIndex: 2,
    explanation: "Não se soma diretamente uma string a um inteiro; converta um dos operandos conforme a intenção.",
  ),
  Mission(
    id: "debug-006",
    pathId: "debug",
    title: "Sinais de igualdade",
    language: "JavaScript",
    question: "Qual expressão compara tipo e valor em JavaScript?",
    choices: ["a = b", "a == b", "a === b"],
    correctIndex: 2,
    explanation: "=== compara também o tipo e evita coerções implícitas de ==.",
  ),
  Mission(
    id: "debug-007",
    pathId: "debug",
    title: "Loop infinito",
    language: "Python",
    question: "Qual risco de while True: sem condição de saída?",
    choices: ["Nenhum, executa uma vez", "Pode continuar indefinidamente", "Sempre gera SyntaxError"],
    correctIndex: 1,
    explanation: "Sem break ou outra saída, a condição permanece verdadeira e o loop não termina.",
  ),
  Mission(
    id: "debug-008",
    pathId: "debug",
    title: "Limite do range",
    language: "Python",
    question: "Por que range(1, 4) não inclui 4?",
    choices: ["O limite final é exclusivo", "Números pares são ignorados", "O início é exclusivo"],
    correctIndex: 0,
    explanation: "O argumento final de range é exclusivo: a sequência é 1, 2 e 3.",
  ),
  Mission(
    id: "debug-009",
    pathId: "debug",
    title: "Parâmetros",
    language: "Python",
    question: "O que ocorre ao chamar soma(1) se soma exige dois argumentos posicionais?",
    choices: ["O segundo vira zero", "Gera TypeError", "Retorna 1"],
    correctIndex: 1,
    explanation: "Sem valor padrão, o argumento obrigatório ausente provoca TypeError.",
  ),
  Mission(
    id: "debug-010",
    pathId: "debug",
    title: "Array vazio",
    language: "JavaScript",
    question: "Qual é o resultado de [].length em JavaScript?",
    choices: ["undefined", "1", "0"],
    correctIndex: 2,
    explanation: "Um array vazio tem comprimento zero; acessar length não gera erro.",
  ),
  Mission(
    id: "web-001",
    pathId: "web",
    title: "Primeira página",
    language: "HTML",
    question: "Qual elemento representa o título principal de uma página?",
    choices: ["<h1>", "<p>", "<span>"],
    correctIndex: 0,
    explanation: "h1 é o cabeçalho de maior nível semântico; use títulos com hierarquia apropriada.",
  ),
  Mission(
    id: "web-002",
    pathId: "web",
    title: "Links",
    language: "HTML",
    question: "Qual atributo define o destino de um link <a>?",
    choices: ["src", "href", "alt"],
    correctIndex: 1,
    explanation: "O atributo href indica o endereço de destino do link.",
  ),
  Mission(
    id: "web-003",
    pathId: "web",
    title: "Estilo",
    language: "CSS",
    question: "Qual propriedade CSS altera a cor de um texto?",
    choices: ["color", "background-image", "margin"],
    correctIndex: 0,
    explanation: "A propriedade color controla a cor do conteúdo textual.",
  ),
  Mission(
    id: "web-004",
    pathId: "web",
    title: "Constantes",
    language: "JavaScript",
    question: "O que impede reatribuição de uma variável declarada com const?",
    choices: ["const", "var", "let"],
    correctIndex: 0,
    explanation: "const impede reatribuir a vinculação; isso não congela automaticamente objetos e arrays.",
  ),
  Mission(
    id: "web-005",
    pathId: "web",
    title: "Console",
    language: "JavaScript",
    question: "Qual comando escreve uma mensagem no console do navegador?",
    choices: ["print('oi')", "console.log('oi')", "echo 'oi'"],
    correctIndex: 1,
    explanation: "console.log envia mensagens ao console de desenvolvimento do JavaScript.",
  ),
]; nums[2]?',
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
        _completed = AcademyProgress(
          prefs.getStringList(progressKey) ?? <String>[],
          missions.map((mission) => mission.id),
        ).completed;
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
    final progress = AcademyProgress(_completed, missions.map((m) => m.id));
    final completedCount = progress.completedCount;
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
              applicationVersion: '0.2.0',
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
                            Text('${progress.xp} XP',
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
                  const SizedBox(height: 20),
                  _ProgressPanel(progress: progress),
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

class _ProgressPanel extends StatelessWidget {
  const _ProgressPanel({required this.progress});
  final AcademyProgress progress;

  @override
  Widget build(BuildContext context) {
    final remaining = progress.nextLevelAt == null
        ? null
        : progress.nextLevelAt! - progress.completedCount;
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFF32415C)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.military_tech_outlined,
                    color: WolfpackAcademyApp.accent),
                const SizedBox(width: 10),
                Expanded(
                  child: Text('Nível ${progress.level} • ${progress.title}',
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(remaining == null
                ? 'Você alcançou o nível máximo da Beta 0.2!'
                : 'Faltam $remaining missões para o próximo nível.',
              style: const TextStyle(color: Color(0xFFB1BDD0))),
            const SizedBox(height: 12),
            LinearProgressIndicator(
              value: progress.levelFraction,
              minHeight: 7,
              borderRadius: BorderRadius.circular(8),
            ),
            const SizedBox(height: 18),
            const Text('Conquistas',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final badge in progress.achievements.entries)
                  Chip(
                    avatar: Icon(
                      badge.value ? Icons.verified : Icons.lock_outline,
                      color: badge.value
                          ? const Color(0xFF6DE7B4)
                          : const Color(0xFF98A8C0),
                      size: 18,
                    ),
                    label: Text(badge.key),
                    backgroundColor: badge.value
                        ? const Color(0xFF173F3B)
                        : const Color(0xFF26324A),
                    side: BorderSide.none,
                    labelStyle: TextStyle(
                      color: badge.value
                          ? const Color(0xFFE5FFF7)
                          : const Color(0xFFB4C2D5),
                    ),
                  ),
              ],
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
                  subtitle: Text('${available[i].language} • Desafio interativo'),
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
      appBar: AppBar(title: Text('${mission.language} • Missão')),
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
                    Text(correct ? '✓ Resposta correta!'
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
              if (!correct) ...[
                OutlinedButton.icon(
                  onPressed: () => setState(() => _selected = null),
                  icon: const Icon(Icons.replay),
                  label: const Text('Tentar novamente'),
                ),
                const SizedBox(height: 10),
              ],
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
