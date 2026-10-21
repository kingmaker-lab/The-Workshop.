# Heart

Nucleo local para percepção, estado, memória e ações controladas.

## Executar

```bash
python3 -m heart
python3 -m heart --once
python3 -m unittest discover -s tests -v
```

O MVP usa apenas a biblioteca padrão do Python. Sensores Linux leem `/proc` e `/sys` quando disponíveis, e eventos são persistidos em SQLite em `data/heart.db`.

## Tool Router

Intenções chegam ao Heart como objetos estruturados e passam pelo `ToolRouter`. As ferramentas disponíveis por padrão são `system_status`, `run_script`, `start_process` e `send_notification`. Scripts e processos usam allowlists; não existe execução de shell arbitrário. Cada pedido é validado, submetido à política de permissões e registrado no audit log.

Exemplo:

```python
from heart import Heart

heart = Heart()
result = heart.dispatch_tool({"tool": "system_status", "arguments": {}})
print(result.result)
```

## Princípios

- sensores produzem dados estruturados sem chamar o modelo;
- eventos importantes são registrados antes de qualquer interpretação;
- ações são explicitamente classificadas por risco;
- ações de nível 2 ou 3 exigem confirmação;
- o executor não aceita shell arbitrário.


## HEART_002 — Memória conversacional persistente

O módulo `heart.conversation.ConversationStore` mantém sessões e mensagens (papéis
`system`, `user`, `assistant`, `tool`) em SQLite, no mesmo banco local
do monitoramento, em tabelas separadas. Possui histórico paginado por limite,
isolamento por sessão e busca literal. Não envia dados à rede. Ainda não está
ligado automaticamente ao roteamento do runtime: a API é opt-in.

```python
from heart.conversation import ConversationStore
with_store = ConversationStore("data/heart.db")
session = with_store.create_conversation()
with_store.add_message(session, "user", "Olá Heart")
print(with_store.recent(session))
with_store.close()
```

## HEART_003 — Tokenizer autoral Byte-BPE

`heart.neural.BPETokenizer` implementa Byte Pair Encoding determinístico
sobre bytes UTF-8. Treina merges apenas com o corpus passado pelo usuário,
preserva Unicode sem token desconhecido e pode salvar/carregar um vocabulário
JSON versionado. É uma implementação educacional, não um LLM ou modelo neural treinado.

```python
from heart.neural import BPETokenizer
tokenizer = BPETokenizer()
tokenizer.train(["Olá coração", "coração e ciência"] * 20, vocab_size=320)
tokens = tokenizer.encode("Olá coração")
assert tokenizer.decode(tokens) == "Olá coração"
tokenizer.save("data/tokenizer.json")
```

### Demonstração e testes

A partir de `IA/Heart`:

```bash
python3 -m scripts.heart_experiments
python3 -m unittest discover -s tests -v
```

Os arquivos de banco e vocabulário produzidos em `data/` são locais e não
devem ser publicados no Git. Nunca alimentar o treinamento com segredos.
A geração textual por rede neural será abordada em experimentos posteriores.
