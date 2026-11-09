# Wolfpack Academy • Gate de publicação Google Play

**Estado:** beta técnico / APK de testes. **Não publicar em produção sem cumprir os gates.**

## Base técnica já existente

- [x] App Flutter com interface própria (sem WebView).
- [x] Conteúdo educacional local e offline; sem conta ou analytics.
- [x] Trilha de lógica e caça aos bugs, com cinco desafios, feedback e XP.
- [x] Workflow de análise, teste e compilação de APK de desenvolvimento.
- [ ] Validar APK em aparelhos Android reais e versões de Android diferentes.
- [ ] Testes de acessibilidade com leitor de tela, fonte ampliada, contraste e navegação por teclado.
- [ ] Testes de rotação, retomada em segundo plano, estado persistido e atualização do app.
- [ ] Revisão pedagógica de desafios e explicações.

## Google Play (requisitos atuais, conferir novamente antes de enviar)

- [ ] Definir titular da conta Play Console (pessoa física ou organização).
- [ ] Escolher package/application ID definitivo (o starter gera `dev.wolfpackworkshop.wolfpack_academy`).
- [ ] **Target API >= 36 (Android 16)** para novos envios a partir de 31/08/2026 (salvo exceções oficiais).
- [ ] Fixar versão de Flutter/Android SDK no CI antes de build de produção e registrar lockfile.
- [ ] Configurar ícone, splash, nome na launcher, ficha da loja e capturas reais de tela.
- [ ] Gerar e guardar upload keystore fora do repositório; habilitar Play App Signing.
- [ ] Criar variante release assinada e `flutter build appbundle --release` (AAB) com versionCode crescente.
- [ ] Revisar formulários: segurança dos dados, política de privacidade, público-alvo, classificação, conteúdo de app e publicidade.
- [ ] Decidir se o app será dirigido a crianças: se sim, revisar requisitos adicionais Google Play Families.
- [ ] Executar teste interno com APK/AAB e solicitar avaliação dos testadores.
- [ ] Se conta pessoal criada após 13/11/2023, teste fechado com pelo menos 12 testadores inscritos por 14 dias consecutivos antes de solicitar acesso a produção.
- [ ] Corrigir erros, checar travamentos/ANRs, consumo de bateria e permissões.
- [ ] Reavaliar dependências, licenças, cadeia de suprimentos, dados e segurança; aprovar release gate interno.

**Não incluir secrets, keystores, dados pessoais ou certificados privados nos commits ou artifacts públicos.**

## Privacidade (estado de v0.1)

O protótipo atual salva somente missões concluídas nas preferências do dispositivo. Não faz login, chamadas de rede, publicidade nem analítica. Antes de publicar, conferir manifesto final, plugins, políticas e fluxos reais; elaborar e hospedar política de privacidade acessível. Se futuramente conectarmos Render ou Cloudflare, reavaliar transmissão, retenção, autenticação e LGPD.

## Distribuição

- GitHub Actions: artifact `wolfpack-academy-debug-apk` é para testes e pode ser baixado na execução concluída.
- APK debug **não** equivale a AAB de produção.
- O teste interno da Play Store também requer cadastro e configuração no console.

## Fontes oficiais

- https://docs.flutter.dev/deployment/android
- https://support.google.com/googleplay/android-developer/answer/11926878?hl=pt-BR
- https://support.google.com/googleplay/android-developer/answer/14151465?hl=pt-BR
