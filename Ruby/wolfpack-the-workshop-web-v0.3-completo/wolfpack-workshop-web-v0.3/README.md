# WolfPack — The Workshop v0.3 · Visual Fix

**Ruby Protocol + VULPES-77 · plataforma estática e autocontida.**

## Correção de publicação

O CSS principal foi comparado entre v0.1 e v0.2 e é idêntico. Como o visual
quebrou após o deploy anterior, esta versão evita a dependência de caminhos
externos para a identidade visual e os jogos.

**Todo CSS, as 12 lições Ruby, as missões VULPES e os scripts da interface estão
embutidos no `index.html`.** Apenas a execução de Ruby/WASM utiliza o arquivo
`js/ruby-worker.js` (incluído no ZIP).
O motor Ruby WebAssembly é carregado sob demanda de um CDN fixado (precisa internet)
pelo `js/ruby-worker.js` da mesma origem. Há um fallback embutido para
visualizações locais. As outras funções do site não precisam desse arquivo. O VULPES-77 é 100% local e não
precisa de rede. As fontes remotas são opcionais, com fallbacks locais.

Não confundir: **o CSS embutido resolve o carregamento do design**, mas não
permite afirmar que o deploy público da sua conta Cloudflare já foi testado.

## Publicação

1. Cloudflare Dashboard → Workers & Pages → Upload Static Assets / Pages Direct Upload.
2. Envie `wolfpack-workshop-cloudflare-v0.3-visual-fix.zip`, que contém `index.html`
   na raiz e os downloads originais.
3. Confira a versão no rodapé: `BUILD 0.3.0 · VISUAL FIX`.
4. Abra uma aba anônima ou use Ctrl+Shift+R, teste `#vulpes`, `#jogar` e o mobile.

Caso o Cloudflare ofereça escolha entre **Worker de código** e **projeto estático**, escolha
hospedar os arquivos estáticos; **não** cole HTML no editor de código Worker.

## Localmente

```bash
python3 -m http.server 8000
# http://localhost:8000/
```

Também é possível abrir `index.html` diretamente como arquivo local para
visualização e para jogar VULPES-77. Para executar Ruby, abra com servidor HTTP;
o carregamento WebAssembly depende de CDN e das permissões do navegador.

## Política de segurança

VULPES-77 é uma simulação local de rede NEXUS; nunca varre hosts reais. O Ruby
Protocol roda código arbitrário no browser via WebAssembly: não tratar isso
como sandbox completa para código hostil. Progresso salvo em `localStorage`.

## Origem e paridade

- O código `js/` e `data/` permanece disponível no projeto completo para manutenção.
- Os dados do VULPES vêm do motor original Ruby, e as regras mantêm o port v0.2.
- As chaves de save não foram alteradas; devem preservar o progresso v0.1/v0.2
  no mesmo domínio e navegador. Ao trocar de domínio, o save anterior não migra sozinho.
