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
