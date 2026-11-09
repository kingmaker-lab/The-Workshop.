# Wolfpack Academy • Android Beta v0.2

Primeira aplicação mobile real da The Workshop (Flutter + Material 3), **não é WebView**.

## Recursos incluídos

- Home nativa, trilhas de Lógica e Caça aos Bugs.
- 25 missões educacionais offline em Python, JavaScript, HTML e CSS, em 3 trilhas.
- Feedback contextual de acertos e erros, com explicação.
- XP, 5 níveis e 5 conquistas calculados a partir de missões únicas concluídas; progresso persistido localmente com `shared_preferences`.
- Compatível com a chave de armazenamento da v0.1 (`completed_missions_v1`), sem zerar histórico ao atualizar o app.
- Módulo independente `lib/progression.dart` e testes de regressão de marcos e migração.

**Importante:** para atualizar a instalação v0.1, instale com mesmo applicationId e assinatura de debug, sem desinstalar. Uma nova instalação ou mudança de assinatura/package pode perder o progresso local.
- Sem login, anúncios, dados pessoais enviados ou chamadas de rede.

O conteúdo é demonstrativo, deve passar por revisão pedagógica e acessibilidade antes de publicação.

## Preparação no Linux

Necessário Flutter SDK e Android SDK configurados. Verifique com:

```sh
flutter doctor
cd mobile/apps/wolfpack_academy
flutter create --platforms=android --org dev.wolfpackworkshop --project-name wolfpack_academy .
flutter pub get
flutter analyze
flutter test
flutter run
```

O comando `flutter create` completa os arquivos Android de plataforma a partir das ferramentas oficiais, sem `--overwrite`.

## APK para testes

```sh
flutter build apk --debug
```

Ou use o artifact `wolfpack-academy-debug-apk` gerado pelo workflow GitHub Actions. **Esse arquivo é de testes, não deve ser publicado na Play Store**.

## Preparação para publicação na Google Play

1. Escolher definitivamente o `applicationId` Android antes da primeira publicação (gerado provisoriamente a partir de `dev.wolfpackworkshop`).
2. Criar conta Google Play Console (pessoa física ou organização) e verificar requisitos atuais de cadastro.
3. Revisar suporte, privacidade, classificação etária, conteúdo do app, política de dados e ficha da loja.
4. Configurar keystore de upload com armazenamento seguro, sem commit em Git, e Play App Signing.
5. Gerar **AAB release assinado**: `flutter build appbundle --release`.
6. Enviar para teste interno e, se aplicável, teste fechado com os requisitos da conta; resolver bugs e solicitar publicação.

Documentação oficial:
- https://docs.flutter.dev/deployment/android
- https://support.google.com/googleplay/android-developer/answer/14151465?hl=pt-BR

## Depois do Android

O mesmo código Flutter será a base da versão iOS, exigindo compilação com macOS/Xcode, conta Apple Developer e processo TestFlight/App Store. Não há build iOS nesta branch.

## Escopo e pendências

- Não integra ainda a API no Render; o aplicativo é intencionalmente offline-first.
- Não contém avaliações reais de Android físico, relatório de acessibilidade ou builds validados no momento da criação.
- CI compila um **APK debug** e testa o código, mas não possui segredos para assinar AAB de produção.
- Revisar nome, imagens, splash, ícone, licença do conteúdo, proteção de dados e testes com alunos.
