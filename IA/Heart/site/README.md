# ARGUS Protocol — HeartAI public lab

Página pública estática do primeiro projeto ARGUS na bancada do The Workshop.

- Arquivo: `argus/index.html`
- URL-alvo: `https://workshop-labs.pages.dev/argus/`
- Demonstração do tokenizer: **simulação didática no navegador** com merges treinados a partir de corpus fixo, sem chamadas a APIs.
- Runtime Linux, SQLite e ferramentas de agente **não são expostos**.
- HEART_001-003 representam código existente; os experimentos seguintes estão planejados.

Para hospedar no projeto Cloudflare Pages `workshop-labs`, inclua `argus/index.html` no diretório de publicação ao lado do `index.html` atual e acrescente um card no portal apontando para `/argus/`.

O Pages atual é Direct Upload; um commit neste repositório sozinho **não** desencadeia atualização automática da página pública.
