# ADR 001 · Uma transação por revisão

**Status** Aceito para o primeiro incremento.

Um único processo Python por comando acessa o banco SQLite local. Cada transação usa `BEGIN IMMEDIATE` e `synchronous=FULL`. A geração mais alta é a revisão ativa. A inserção da revisão e a ativação passam a valer no mesmo commit. A recuperação materializa uma nova revisão e registra de onde vieram os valores.

A decisão mantém a operação em Debian leve e elimina a necessidade de sincronizar um ponteiro ativo em outro arquivo. Depende do armazenamento local e serializa operações, inclusive consultas pelo adaptador atual. Alta disponibilidade e retenção serão avaliadas com dados da primeira integração consumidora.
