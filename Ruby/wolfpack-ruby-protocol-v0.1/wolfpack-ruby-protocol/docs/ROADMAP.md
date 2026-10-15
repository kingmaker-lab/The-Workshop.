# WOLFPACK — Ruby Protocol | Roadmap

## v0.1 — The Awakening ✅
- 12 missões em história guiada, com conteúdo progressivo.
- Ruby real via interpretador local, casos de teste automatizados.
- Progressão de 100 XP por missão; desbloqueio sequencial.
- Persistência JSON, mapa de evolução, dicas e soluções.
- Zero gems externas.

## v0.2 — The Hunt (planejado)
- Corrigir desafios aceitando formas mais amplas de solução via AST com `Ripper`.
- Missões de booleanos, `case`, ranges, `while`, exception (`begin/rescue`), módulos, require e gems.
- Códigos das missões exportados para arquivos `.rb` e reexecução voluntária.
- Menu de repetição de aulas e estatísticas de aprendizagem.
- Editor via `$EDITOR` opcional.

## v0.3 — The Pack (planejado)
- Classes ARES, ARGUS, RAVEN e CERBERUS como trilhas, sem bloquear o currículo básico.
- Especializações: automação, parsing, CLI, APIs, testes com Minitest.
- Quests com decisões e consequências, missões de laboratório e chefes.
- TUI com `curses` opcional, mantendo modo simples.

## v1.0 — The Workshop Academy (planejado)
- Executor protegido por contêiner isolado, sem rede e com usuário não privilegiado.
- Modo educador: criação de novas missões sem mexer no core.
- Relatório de evolução e exportação de aprendizagem.

### Princípio de design
Cada fase deve ter **explicação → exemplo → código do aluno → feedback de execução → aprendizado**. Nenhuma mecânica deve roubar protagonismo do Ruby.
