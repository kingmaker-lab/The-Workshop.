# ADR 002 · Autenticação local e controle de geração

**Status** Aceito para o primeiro incremento.

O CLI autentica envelopes e revisões com HMAC-SHA-256 e domínios distintos. A geração esperada integra o envelope autenticado. A revisão cobre política, geração, ação e referência à origem quando houver recuperação. Validação por esquema rejeita campos extras, tipos incorretos e limites fora da política. A chave é gerada localmente e protegida pelas permissões do arquivo.

A decisão suporta operação individual sem infraestrutura de identidade. Aprovação independente, rotação, identificação de operadores e prova de continuidade do histórico dependem do modelo de confiança exigido pelo serviço consumidor.
