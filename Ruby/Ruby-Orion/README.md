# 💎 Ruby Orion | The Workshop

> **Three Stars. Infinite Possibilities.**

Uma iniciativa de engenharia e aprendizado sobre Ruby, estruturada em três pilares inspirados nas estrelas do cinturão de Órion:

- **Alnitak / Learn:** compreender os fundamentos da linguagem.
- **Alnilam / Build:** construir ferramentas úteis e reutilizáveis.
- **Mintaka / Explore:** investigar sistemas, redes, desempenho e limites técnicos.

## v0.1 · Alnitak / Foundation

CLI escrito em Ruby puro (Ruby 3.1+), sem dependências externas em tempo de execução.

```sh
ruby -Ilib bin/orion help
ruby -Ilib bin/orion --version
ruby -Ilib bin/orion info --json
ruby -Ilib bin/orion inspect README.md --json
ruby -Ilib bin/orion hash README.md --algorithm sha256
ruby -Ilib bin/orion hash README.md --verify "SEU_DIGEST_SHA256_HEX"
ruby -Ilib bin/orion labs
ruby labs/001-object-model/example.rb
```

Instalar como gem local, sem publicação automática no RubyGems:

```sh
gem build ruby-orion.gemspec
gem install ./ruby-orion-0.1.0.gem
orion help
```

## Testes

```sh
ruby -Ilib -Itest -e 'Dir["test/test_*.rb"].sort.each { |file| require_relative file }'
```

## Segurança

- CLI opera em arquivos **locais**, somente leitura.
- Não executa código arbitrário, não faz chamadas de rede e não envia hashes a serviços externos.
- Arquivos especiais e links simbólicos são recusados; o descritor aberto é validado. A amostragem para inspeção é limitada a 4 KiB e os hashes usam leitura por blocos de 64 KiB.
- A análise de assinatura é apenas heurística; não substitui um parser de binário nem comprova que o arquivo é seguro.
- Os laboratórios planejados são identificados como planejados; o EXP-001 está implementado.

## Organização

```text
bin/orion                   CLI
lib/orion/                 núcleo Ruby, inspeção e inventário
labs/001-object-model/     laboratório inicial
test/                      testes Minitest
docs/ROADMAP.md             releases planejados
```

**Repositório:** incubado em `The-Workshop./Ruby/Ruby-Orion/`, autocontido e pronto para extração futura para `kingmaker-lab/Ruby-Orion`. Ainda não existe repositório independente.

MIT License · The Workshop
