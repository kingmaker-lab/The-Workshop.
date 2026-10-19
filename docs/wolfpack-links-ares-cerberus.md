# WolfPack OS — linkagem ARES + CERBERUS

## Alteração solicitada

O card **ARES** deve abrir:
`https://workshop-labs.pages.dev/projects/ares/`

O card **CERBERUS** deve abrir:
`https://cerberus.wolfpackworkshop.workers.dev/`

Os dois cards são links HTML nativos (sem JavaScript, iframe ou redirecionador), com `rel="noopener noreferrer"`, `referrerpolicy="no-referrer"`, texto de acesso claro e navegação por teclado. Cerberus é **Arquitetura de Software**, não orquestração.

## ⚠ Atenção à produção

Em 2026-10-19, o Worker `wolfpack` já servia **WolfPack OS v0.4.0**, contendo **RAVEN Drift Lab**. A versão do site encontrada no GitHub (`Ruby/wolfpack-the-workshop-web-v0.3-completo/wolfpack-workshop-web-v0.3/index.html`) é **v0.3**, mais antiga que o live.

Esta mudança atualiza o repositório v0.3 de referência, **não garante alteração no Worker live**. A versão v0.4.0 não pode ser reconstruída integralmente a partir deste conteúdo sem perder funcionalidades do RAVEN. Não executar `wrangler deploy` nem substituir o script `wolfpack` com o HTML antigo.

### Publicação segura da v0.4

1. Obter **backup completo do código v0.4.0 que está publicado** no Dashboard Cloudflare > Workers & Pages > wolfpack > Edit Code (ou fluxo equivalente de exportação autorizado).
2. Versionar esse código, junto com assets dependentes, em diretório próprio `web/wolfpack-os-v0.4`.
3. Aplicar **somente** as alterações aos cards ARES e CERBERUS no arquivo da versão v0.4, sem alterar os scripts/estados de Ruby Protocol, VULPES-77 e RAVEN.
4. Rodar testes de navegação e segurança; verificar status e links dos dois destinos, sem inventar disponibilidade.
5. Publicar a nova versão usando preview ou deploy gradual; validar o site em produção e manter rollback disponível.

### Gate local no repositório

```bash
python -m unittest discover -s Ruby/wolfpack-the-workshop-web-v0.3-completo/wolfpack-workshop-web-v0.3/tests -p 'test_card_links.py'
```

Outras experiências continuam independentes; links não compartilham cookies, tokens, armazenamento local ou CORS entre os sites.
