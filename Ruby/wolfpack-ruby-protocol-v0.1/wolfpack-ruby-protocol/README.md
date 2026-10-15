# 🐺 WOLFPACK // RUBY PROTOCOL

**The Workshop • Kingmaker • Terminal Game**

Um jogo **100% em terminal** para aprender Ruby, do zero, escrevendo programas de verdade. A missão da Matilha: restaurar os sistemas de uma base invadida, aprendendo uma engrenagem da linguagem a cada etapa.

> **Você não assiste à aula. Você escreve o código que abre a próxima porta.**

## Começar em 30 segundos

Requisito: **Ruby 3.x** instalado (testado em Ruby 3.3.8). Não usa gems externas.

```bash
ruby --version
cd wolfpack-ruby-protocol
ruby play.rb
```

Em sistemas Unix, `./play.rb` também funciona.

O jogo pede um **codinome**, explica o conceito, oferece um exemplo e abre um editor simples. Escreva o código; digite `FIM` sozinho numa linha para testar. Se funcionar e atender aos requisitos, ganha **100 XP** e desbloqueia a próxima missão.

### Exemplo: primeiro desafio

```text
[1/12] O primeiro uivo | puts
DESAFIO: Mostre exatamente: A matilha despertou!

comando> [ENTER]
01 | puts "A matilha despertou!"
02 | FIM

✅ 1 teste(s) passaram! Código validado. +100 XP
```

## Campanha: 12 missões, quatro atos

| Missão | Conceito Ruby | Na história |
|---|---|---|
| 01 | `puts`, Strings | Despertar o terminal |
| 02 | Variáveis, interpolação `#{...}` | Escolher o codinome |
| 03 | Inteiros, operadores | Calcular energia |
| 04 | `gets`, `chomp` | Receber um integrante |
| 05 | `if`, `else`, `end` | Abrir o portão |
| 06 | `.times`, blocos | Coordenar a marcha |
| 07 | Arrays, índices | Formar o esquadrão |
| 08 | Hashes, Symbols | Ler a telemetria |
| 09 | `.each`, blocos | Patrulhar a base |
| 10 | `def`, parâmetros, retorno | Assinar um selo |
| 11 | `class`, `initialize`, `@instância` | Criar um lobo |
| 12 | Integração de conceitos | Restaurar o protocolo Kingmaker |

O ensino é **progressivo**: primeiro o jogo mostra um exemplo, depois exige que o jogador escreva uma solução, e finalmente testa o resultado. As missões 4, 5, 10, 11 e 12 usam **múltiplas entradas de teste** para evitar soluções que funcionem apenas com um nome ou número.

## Comandos

| Comando | Quando usar |
|---|---|
| `ENTER` | Abre o editor do desafio |
| `FIM` | Finaliza o código e executa os testes |
| `:dica` | Pista para o desafio |
| `:exemplo` | Mostra novamente o exemplo da aula |
| `:solucao` | Mostra uma solução para estudar |
| `:voltar` | Sai da missão e retorna à central |
| `CANCELAR` | Cancela a edição, se for a primeira linha |
| `Ctrl+C` | Encerra o jogo; o progresso já concluído permanece salvo |

A central permite continuar, visualizar o **mapa**, ler o manual, reiniciar ou sair.

## Salvar e continuar

O progresso fica em `~/.wolfpack_ruby/progress.json` e é salvo após cada missão. Por padrão, cada missão concluída rende 100 XP. É possível personalizar o caminho para desenvolvimento e testes:

```bash
WOLFPACK_SAVE_PATH=./progresso-local.json ruby play.rb
```

O jogo nunca executa automaticamente trechos de outros usuários; você escolhe o que digitar.

## Como funciona por dentro

```text
wolfpack-ruby-protocol/
├── play.rb                       # Ponto de entrada
├── lib/wolfpack/
│   ├── game.rb                   # Menus, editor, narrativa, experiência
│   ├── lessons.rb                # 12 lições, exemplos, desafios e casos de teste
│   ├── runner.rb                 # Execução de Ruby em subprocesso + comparação
│   └── progress.rb               # Salvamento do jogador (JSON)
├── test/
│   └── test_wolfpack.rb          # Testes automatizados
├── docs/
│   └── ROADMAP.md                # Evolução da oficina
└── README.md
```

O avaliador exige que a solução produza a **saída esperada** em todos os cenários e também procura estruturas didáticas importantes (`if`, `each`, `def`, etc.). Essas verificações de presença são **orientativas**, não uma análise formal de AST; soluções equivalentes que utilizem outra técnica podem não ser aceitas. Se isso acontecer, reveja a técnica específica que a missão pretende ensinar.

### Segurança da execução — importante

**Este projeto não é uma sandbox de segurança.** O código Ruby digitado é executado **localmente na sua máquina** em um novo processo, com limite aproximado de **3 segundos** e de **16 KiB de saída**. Esses limites reduzem alguns erros acidentais, **mas não impedem** leitura de arquivos, conexões de rede ou comandos do sistema. **Nunca cole ou execute código Ruby de procedência desconhecida.** Para um laboratório multiusuário, uma futura versão precisará de isolamento real (contêiner sem rede, usuário sem privilégios, filesystem temporário e limites de recursos).

## Testes automatizados

```bash
ruby test/test_wolfpack.rb
```

Há cobertura para soluções das 12 missões, exemplos, respostas incorretas, erro de sintaxe, loop infinito, persistência e primeira missão pela interface.

## Próximos passos

Veja [docs/ROADMAP.md](docs/ROADMAP.md) para expansão do jogo: lições de exceptions, módulos, hashes mais complexos, novos biomas, laboratório isolado, editor de arquivos, achievements e progressão por especialidades **ARES / ARGUS / RAVEN / CERBERUS**.

**WOLFPACK. Escrever, executar, entender.** 👑
