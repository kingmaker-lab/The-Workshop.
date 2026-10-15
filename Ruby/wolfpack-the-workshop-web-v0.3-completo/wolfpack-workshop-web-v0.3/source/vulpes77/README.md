# VULPES-77: INCIDENT ZERO 🦊

**Terminal Cybersecurity RPG — The Workshop**

**Ruby | v0.1.0 | Jogo independente e 100% simulado**

Um game narrativo de investigação de incidentes de segurança, que roda inteiramente no terminal. Você assume o papel de um analista SOC na rede fictícia **NEXUS**: descobre ativos, investiga evidências, correlaciona eventos, decodifica mensagens e toma decisões de contenção.

> **Segurança:** o game nunca usa sockets, executa ferramentas do sistema, escaneia IPs reais ou se conecta à internet. `scan`, `connect` e `contain` são comandos interpretados exclusivamente pelo mecanismo do jogo. Os IPs `10.77.0.x` são apenas identificadores da rede fictícia e `203.0.113.x` é uma faixa reservada para documentação.

## Requisitos

- Ruby >= 3.1 (biblioteca padrão; **sem gems adicionais**).
- Linux, macOS ou Windows com Ruby instalado.

## Jogar

```bash
cd vulpes77-terminal
ruby bin/vulpes77
```

Ou, no Linux/macOS:

```bash
./bin/vulpes77
```

**Nova campanha:** `ruby bin/vulpes77 --new`

**Sem cores ANSI:** `ruby bin/vulpes77 --no-color`

**Save customizado:** `ruby bin/vulpes77 --save ./save.json`

**Progresso:** salvo automaticamente em `~/.vulpes77/save.json` após comandos executados. Se você jogou a versão anterior, o progresso em `~/.ghostwire/save.json` será importado automaticamente na primeira inicialização, sem apagar o arquivo antigo. `--new` inicia uma campanha nova. Também há um comando `save` dentro do jogo.

## Comandos

| Comando | Função |
|---|---|
| `help` | Ajuda |
| `map` | Mapa da rede fictícia |
| `scan <IP>` | Examina portas simuladas de um host |
| `connect <IP>:<porta>` | Abre sessão com um serviço do jogo |
| `ls` / `cat <arquivo>` | Examina evidências e arquivos |
| `grep <termo> <arquivo>` | Filtra evidências textuais |
| `decode b64 <valor>` | Decodifica Base64 |
| `decode hex <valor>` | Decodifica hexadecimal |
| `hash sha256 <texto>` | Calcula SHA-256 localmente |
| `contain <IP>` | Isola um host autorizado na missão final |
| `submit <resposta>` | Envia uma solução |
| `hint` | Exibe dica com penalidade de 15 pontos |
| `status` / `journal` | Pontos e histórico |
| `save` / `novo` / `sair` | Salva, reinicia ou sai |

### Início de uma sessão (sem spoilers)

```text
vulpes77@nexus$ map
NEXUS / SEGMENTO DE TREINAMENTO
10.77.0.1     GATEWAY    [ONLINE]
10.77.0.12    WEB-01     [ONLINE]
10.77.0.23    LOG-01     [BLOQUEADO]
10.77.0.44    SEC-CTRL   [BLOQUEADO]

vulpes77@nexus$ scan 10.77.0.12
WEB-01 (10.77.0.12)
80/tcp open public-site
8080/tcp open telemetry-console
```

## Campanha

1. **O Eco Fantasma** — análise de telemetria, descoberta de serviços, Base64.
2. **Sombras nos Logs** — correlação de logs e atribuição baseada em evidências.
3. **Silêncio Operacional** — documentação, decisão de contenção e registro de ticket.

Cada missão vale até **100 pontos**. Dicas reduzem a pontuação em 15; respostas incorretas, em 5. Ao final, o jogador ganha uma patente conforme a pontuação total.

## Arquitetura

```text
vulpes77-terminal/
├── bin/vulpes77       # Interface interativa e cores ANSI
├── lib/vulpes77.rb    # Motor do game, mundo virtual, puzzles e save
├── test/test_game.rb   # Testes automatizados (Minitest)
├── README.md
└── LICENSE
```

O motor é independente da interface, facilitando novas missões, inventários, NPCs e outras mecânicas em versões futuras. O estado é serializado em JSON.

**Identidade:** nome, banner, módulo Ruby, executável, documentação e diretório de save foram atualizados para VULPES-77. A rede fictícia NEXUS e os puzzles originais foram preservados.

## Testes

```bash
ruby -Ilib test/test_game.rb
```

## Próximos passos (ideias)

- Adversários com ações em turnos; um relógio simulado de incidente.
- Procedimentos de hardening, regras de detecção e análise de artefatos.
- Novas campanhas em arquivos JSON validados.
- Replay de missões, conquistas e seleção de dificuldade.

**O terminal é o tabuleiro. As evidências são as armas.**
