# HeartAI / Workshop Labs

URL pública: https://workshop-labs.pages.dev/heartai/

O HeartAI é o laboratório local de pesquisa em inteligência artificial do
The Workshop. O projeto **não** é o ARGUS defensivo (threat hunting).

## Endereços e assets

- `/heartai/`: HeartAI / tokenização e embeddings.
- `/heartai/tokenizer.js`: demo Byte-level BPE (HEART_003).
- `/heartai/embeddings.js`: demo com skip-gram de corpus público fixo
  e similaridade de cosseno (HEART_004).
- `/argus/`: projeto de threat hunting defensivo, independente.

Os arquivos `site/argus/index.html`, `site/argus/argus.js` e
`site/argus/embeddings.js` preservam o histórico da antiga nomenclatura.
Sua publicação depende do `web/workshop-labs/_worker.js` agregado. Os
URLs da instalação nova usam `/heartai/`, não `/argus/`.

## Política de publicação

- O Pages `workshop-labs` utiliza **Direct Upload**, sem deploy
  automático do GitHub. Alterar o repositório não atualiza o site.
- Faça deploy de **todo o Worker agregado**, não apenas uma página.
  Caso contrário, as rotas de ARGUS, CERBERUS e demais laboratórios
  podem desaparecer.
- A CSP do HeartAI permite apenas scripts da própria origem,
  `connect-src 'none'`; os outros laboratórios mantêm sua própria CSP.
- Demonstrações executam no navegador, não chamam o runtime Python,
  nem acessam memória SQLite ou ferramentas do computador.
- Os vetores do demo Web **não** são os pesos do protótipo Python;
  ambos são demonstrações didáticas sem validação semântica.

Para reproduzir o treinamento local e os testes Python, consulte
`IA/Heart/README.md`.

A primeira publicação do antigo playground ARGUS/HeartAI é de
2026-10-21. Em 2026-10-30, o HeartAI foi separado no caminho `/heartai/`
para evitar colisões com o ARGUS de segurança.
