# HeartAI — Genesis

> The Workshop | Neural Engineering

## Propósito

Desenvolver um modelo de linguagem autoral, treinado e executado localmente, integrado ao runtime do Heart já existente. Não utilizar APIs externas de inferência. Não confundir memória persistente e regras de intenção com um LLM treinado.

## Estado verificado

O módulo existente reside em `IA/Heart/`, com pacote Python `heart`, `pyproject.toml`, testes, interface de terminal, intenção, contexto, memória, sensores, ferramentas e políticas. O README atual descreve SQLite e um `ToolRouter` que usa allowlists e auditoria. Preservar essas proteções.

## Arquitetura-alvo

- **Runtime**: inicialização, sessão, barramento de eventos e orquestração.
- **Neural**: tokenizer autoral, embeddings, atenção causal, Transformer decoder, treinamento, checkpoints e inferência.
- **Memory**: memória episódica em SQLite e recuperação semântica, independente dos pesos do modelo.
- **Agents**: planejamento e ferramentas com permissão explícita.
- **Security**: políticas de risco, confirmação para ações sensíveis, isolamento e trilha de auditoria.
- **Interfaces**: CLI primeiro; GUI opcional consumindo o mesmo runtime.

## Experimentos

| ID | Experimento | Estado |
|---|---|---|
| HEART_001 | Runtime operacional | Base existente; validar testes |
| HEART_002 | Memória conversacional persistente | Planejado |
| HEART_003 | Tokenizer treinável | Planejado |
| HEART_004 | Embeddings e representações | Planejado |
| HEART_005 | Atenção causal e testes | Planejado |
| HEART_006 | Decoder Transformer | Planejado |
| HEART_007 | Treino autoregressivo e checkpoints | Planejado |
| HEART_008 | Amostragem, geração e avaliação | Planejado |
| HEART_009 | Agentes, planejamento e auditoria | Planejado |
| HEART_010 | Integração operacional Linux em sandbox | Planejado |

## Princípios de segurança e reprodutibilidade

1. Nunca executar código gerado pelo modelo diretamente em shell.
2. Manter ações destrutivas desabilitadas por padrão; exigir autorização granular.
3. Fixar seeds, registrar hiperparâmetros e preservar métricas de treino.
4. Não enviar datasets, bancos privados, tokens ou pesos grandes ao Git.
5. Tratar conteúdo recuperado como dados não confiáveis, não instruções.
6. Nunca aplicar atualização automática de pesos em produção sem avaliação e rollback.

## Execução existente

No diretório `IA/Heart`:

```bash
python3 -m heart
python3 -m heart --once
python3 -m unittest discover -s tests -v
```

A execução de um modelo neural próprio será adicionada somente após testes unitários de arquitetura, treinamento e geração.
