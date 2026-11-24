# 💎 Ruby Orion | The Workshop

> **Three Stars. Infinite Possibilities.**

Iniciativa open source de engenharia e aprendizado em Ruby, organizada pelos três pilares inspirados no cinturão de Órion:

- **Alnitak / Learn:** compreender os fundamentos da linguagem.
- **Alnilam / Build:** construir ferramentas úteis e reutilizáveis.
- **Mintaka / Explore:** investigar sistemas, redes e desempenho.

## v0.2 · Alnilam / Systems Engineering

CLI escrita em Ruby puro **3.3+**, usando bibliotecas padrão, sem gems adicionais em tempo de execução.

```sh
ruby bin/orion --version
ruby bin/orion info --json
ruby bin/orion inspect README.md --json
ruby bin/orion hash README.md --algorithm sha256
ruby bin/orion labs
ruby bin/orion process list --json
ruby bin/orion process run 002 --timeout 5 --json
ruby bin/orion ipc demo --timeout 5 --json
```

**EXP-002:** supervisor de processo filho Ruby confiável com timeout, saída limitada e estado de execução.  
**EXP-003:** troca de mensagens `orion-ipc/1` via pipes com contrato JSON validado.

## Testes e gem

```sh
ruby -Ilib -Itest -e 'Dir["test/test_*.rb"].sort.each { |file| require_relative file }'
gem build ruby-orion.gemspec
# Instalação local, opcional:
gem install ./ruby-orion-0.2.0.gem
orion help
```

## Suporte de versões Ruby

Requer Ruby 3.3 ou superior. Em ambientes reais utilize sempre a versão **mais recente com correções de segurança** da sua série (em novembro de 2026, versões corrigidas: 3.3.14, 3.4.13 e 4.0.10). Versões Ruby 3.1 e 3.2 já alcançaram o fim do suporte oficial. A suíte local desta entrega foi executada com Ruby 3.3.8; o CI verificará versões Ruby mantidas e atualizadas.

## Segurança

A CLI **somente executa scripts cadastrados no código**. Não aceita comando shell ou caminho fornecido pelo usuário para `process run`. O supervisor usa `Open3` com argv separado, ambiente reduzido, relógio monotônico, timeout e coleta de processo; no POSIX cria grupo de processo dedicado. Limites de entrada e saída são aplicados para conter consumo de memória. O protocolo IPC valida estrutura, versão, tamanho e profundidade. Tudo acontece localmente e sem privilégios adicionais.

**Aviso:** Orion Process **não é sandbox**. Não execute código não confiável, não publique a execução por API e não presuma limites rígidos de CPU/RAM/disco ou bloqueio de rede. A política de processos-filhos e limitações estão detalhadas em [docs/ALNILAM.md](docs/ALNILAM.md).

## Organização

```text
bin/orion                     CLI
lib/orion/files.rb            File inspect / hashes
lib/orion/system/             Runner, supervisor, result
lib/orion/ipc/                Frame JSON e canal de pipes
lib/orion/tasks/              Registro estático de tarefas
labs/001-object-model/        Alnitak
labs/002-process-lifecycle/   Alnilam: Process
labs/003-ipc-pipes/           Alnilam: IPC
test/                        Minitest + testes de integração
docs/ALNILAM.md               Especificação de segurança
```

Projeto incubado em [The Workshop](https://github.com/kingmaker-lab/The-Workshop./tree/main/Ruby/Ruby-Orion). O repositório independente `kingmaker-lab/Ruby-Orion` ainda não foi criado. MIT License.
