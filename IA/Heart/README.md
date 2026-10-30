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


## HEART_004 — Token Embeddings experimentais

O módulo `heart.neural.TokenEmbeddings` acrescenta duas tabelas vetoriais
treináveis (centro e contexto), inicialização determinística por seed,
aprendizado local com **skip-gram e negative sampling**, vetorização média
de tokens e cálculo de similaridade por cosseno. É uma implementação didática
em Python puro, sem dependências extras e sem chamadas de rede.

```python
from heart.neural import BPETokenizer, TokenEmbeddings

tokenizer = BPETokenizer()
tokenizer.train(["heartai e linguagem", "pesquisa em inteligencia"] * 10, vocab_size=300)
model = TokenEmbeddings(tokenizer.vocab_size, dimension=8, seed=7)
samples = [tokenizer.encode(s) for s in ["heartai e linguagem", "pesquisa em inteligencia", "aprendizado de tokens"]]
losses = model.fit(samples * 3, epochs=3, window=2, negatives=1)
a = model.mean_pool(tokenizer.encode("heartai"))
b = model.mean_pool(tokenizer.encode("linguagem"))
print(losses, model.cosine(a, b))
```

Os limites de configuração e de cálculo impedem corpora e treinamentos
descontrolados no protótipo. Vetores não são persistidos automaticamente.
A baseline usa amostras fornecidas diretamente pelo pesquisador, nunca
dados reais do computador. **Não existe validação semântica**; os scores
numéricos não demonstram que a IA compreende texto.

O laboratório público integra dois experimentos independentes no navegador:
- [Tokenizer Byte-BPE](https://workshop-labs.pages.dev/heartai/#playground);
- [Embedding Playground](https://workshop-labs.pages.dev/heartai/#embeddings).

O demonstrador web é treinado em um pequeno corpus público fixo e tem
seus próprios vetores efêmeros. Ele não utiliza pesos treinados no Python.

Execute testes a partir de `IA/Heart`:

```bash
python -m unittest discover -s tests -v
python -m scripts.heart_experiments --db /tmp/heart-demo.db --tokenizer /tmp/heart-tokenizer.json
```

Próximo experimento planejado: **HEART_005 Causal Attention**. A arquitetura
não inclui, nesta etapa, Transformer, geração autoregressiva ou modelo de
linguagem treinado.
