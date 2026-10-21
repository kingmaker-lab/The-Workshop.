# CERBERUS 02 — Layers, Clean Architecture & Hexagonal

**The Workshop · Software Architecture Lab · Build. Break. Understand. Rebuild.**

## Pergunta do experimento

**Se trocarmos SQLite por memória (ou a entrada CLI por um controlador JSON), as regras de reserva continuam inalteradas?**

Hipótese: módulos de negócio que dependem apenas de portas abstratas (tipagem estrutural com `Protocol`) podem trocar adaptadores externos sem editar o domínio nem os casos de uso. **Isso não prova escalabilidade, isolamento total ou superioridade universal da arquitetura.**

### As três perspectivas

- **Camadas:** separar domínio, aplicação e infraestrutura, com responsabilidades específicas; nem toda arquitetura em camadas impede dependências descendentes.
- **Clean Architecture:** dependências de código apontam para políticas internas; casos de uso não conhecem banco, web ou CLI.
- **Hexagonal:** portas definem contratos na borda do core; adaptadores de entrada e saída implementam acesso e persistência.

Não são três soluções necessariamente rivais: as três ideias podem coexistir. Inversão de dependências (DIP) é o mecanismo que permite o core expressar sua necessidade por contratos; injeção de dependências é a montagem concreta realizada na borda.

```text
      CLI adapter       JSON controller (no HTTP server)
          |                        |
          +-----> APPLICATION: Create/GetReservation
                              |
                         DOMAIN: Reservation
                              |
                      PORT: ReservationRepository
                         /                  \
                    InMemory             SQLite
```

**Direção de dependência do código:** ambos os adaptadores importam o core; o core nunca importa os adaptadores. O diagrama mostra fluxo de chamadas, não um ciclo de imports.

## Executar (Python 3.11+, somente biblioteca padrão em runtime)

```bash
cd Cerberus/experiments/02-layers-clean-hexagonal
python -m pip install -e .
python -m unittest discover -s tests -v
python -m cerberus02.adapters.cli --backend sqlite --db ./demo.db create --event wolfcon2026 --guest Ada --seats 2
# Copie reservation_id exibido
python -m cerberus02.adapters.cli --backend sqlite --db ./demo.db get --id <id-da-reserva>
```

Para modo memória, substitua `--backend sqlite` por `--backend memory`; o conteúdo desaparece ao encerrar o processo. Para limpar o exemplo SQLite, remova manualmente `demo.db`.

## Protocolo experimental

1. Execute o mesmo caso de uso com `InMemoryReservations` e `SQLiteReservations`.
2. Confirme que as duas implementações passam pelos mesmos testes de contrato.
3. Execute regras inválidas e verifique que nada foi armazenado.
4. Substitua a interface CLI por `ReservationJsonController` (funções Python; **nenhum servidor HTTP é aberto**).
5. Examine o teste AST: `domain.py`, `ports.py` e `usecases.py` não importam infraestrutura.
6. Registre mudanças necessárias, tempo de build/teste e limitações. **Nenhuma medição de performance foi produzida pela documentação.**

## Regras / trade-offs

- `Reservation` imutável; 1 a 6 lugares por requisição; slug público de evento; nome entre 2 e 80 caracteres sem controle ASCII.
- IDs são injetados por `IdGenerator`; em produção, usamos UUID4, nos testes IDs determinísticos.
- SQL usa parâmetros vinculados e `PRIMARY KEY`; **não há controle de capacidade total, transação distribuída, concorrência entre clientes, autenticação ou autorização**.
- Este experimento é **local, didático e não adequado a reservas reais**. `guest_name` seria dado pessoal; não publique bancos SQLite reais nem use PII nos testes.
- Injeção de dependências é composição explícita no adaptador CLI, não um container mágico.
- Teste de arquitetura via AST é um guardrail simples, não uma prova formal da ausência de dependências indiretas.

Veja [ADR-0002](docs/ADR-0002-ports-and-adapters.md) e [Threat model](docs/SECURITY.md).

Portal público do estudo: https://cerberus.wolfpackworkshop.workers.dev/labs/02
