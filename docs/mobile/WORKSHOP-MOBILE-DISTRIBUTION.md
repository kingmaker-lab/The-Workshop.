# The Workshop Mobile · Distribuição oficial Android

Data: 2026-11-10 · Status: **portal publicado**, **assinatura/release pendentes de configuração pelo titular da chave**.

## URLs

- Portal Cloudflare: https://workshop-mobile.wolfpackworkshop.workers.dev/
- Fonte do portal: `web/workshop-mobile/worker.mjs`.
- Release da Academy: `wolfpack-academy-v0.2.0`, com arquivos `wolfpack-academy-v0.2.0.apk`, `wolfpack-academy-v0.2.0.aab`, `SHA256SUMS`.
- Fluxo de publicação: `.github/workflows/wolfpack-academy-release.yml`.
- Ajuste transitório de Gradle: `scripts/mobile/configure_release_signing.py`.

**Não há APK release publicado enquanto as chaves não estiverem configuradas e o workflow manual não for executado na branch main.** A página segura o botão de download até detectar, na API pública do GitHub, o APK exato com digest SHA-256. Não oferece APK debug.

## 1. Gerar e guardar uma chave de produção estável

**Esta etapa deve ser feita pelo responsável pelo aplicativo no próprio computador. Nunca enviar a chave ou as senhas por chat, commitar no GitHub ou disponibilizar em artifact.**

Exemplo Linux com JDK instalado:

```bash
mkdir -p "$HOME/.config/wolfpack-academy"
chmod 700 "$HOME/.config/wolfpack-academy"
keytool -genkeypair -v \
  -keystore "$HOME/.config/wolfpack-academy/academy-release.p12" \
  -storetype PKCS12 -keyalg RSA -keysize 3072 \
  -validity 10000 -alias academy \
  -dname "CN=Wolfpack Academy, OU=The Workshop, O=The Workshop, C=BR"
chmod 600 "$HOME/.config/wolfpack-academy/academy-release.p12"
```

O comando solicitará senha no terminal. Faça ao menos dois backups criptografados, independentes do notebook, de **keystore + senha**. Perder a chave impede atualizações assinadas compatíveis de instalações distribuídas diretamente.

**Não** reaproveitar a chave debug: o aplicativo beta de testes pode ter assinatura diferente em cada runner GitHub Actions.

## 2. Configurar os quatro GitHub Actions Secrets

No repositório `kingmaker-lab/The-Workshop.` → Settings → Secrets and variables → Actions → New repository secret, criar:

| Secret | Conteúdo |
|---|---|
| `ACADEMY_KEYSTORE_B64` | Base64 do arquivo `academy-release.p12` (sem quebras de linha) |
| `ACADEMY_STORE_PASSWORD` | Senha do PKCS12 |
| `ACADEMY_KEY_PASSWORD` | Senha da chave `academy` (normalmente igual à senha do PKCS12) |
| `ACADEMY_KEY_ALIAS` | `academy` |

Para obter o conteúdo base64 sem alterar o arquivo original:

```bash
base64 -w 0 "$HOME/.config/wolfpack-academy/academy-release.p12"
```

**A saída base64 é segredo sensível, não um hash público.** Copiar apenas para o campo secreto no GitHub, em sessão protegida. Não colocar em logs de CI nem em comandos de issue/PR.

Criar, no GitHub → Settings → Environments, um ambiente chamado `android-release` com revisores obrigatórios, se disponíveis, antes de habilitar publicação. Restrinja a branch autorizada a `main`.

## 3. Publicar somente depois das revisões e merges

Ordem de integração: PR #21 (v0.1) → PR #36 (Beta 0.2) → PR da distribuição Mobile. Depois revisar os testes do pipeline.

No GitHub → Actions → **Wolfpack Academy - Signed Release** → Run workflow em `main`, fornecer `RELEASE_V0_2_0`.

A automação então:

1. confere `version: 0.2.0+2`;
2. instala a chave exclusivamente no runner efêmero;
3. executa `flutter analyze` e `flutter test`;
4. configura compileSdk/targetSdk 36;
5. gera APK/AAB de release assinados;
6. valida as assinaturas com `apksigner` e `jarsigner`;
7. gera `SHA256SUMS`, publica arquivos no GitHub Releases e destrói a cópia local da chave.

O portal consulta o GitHub a cada carregamento e mostra download e SHA-256 somente quando o release assinado aparecer. Não coloca credenciais nem lógica de download no navegador.

## 4. Verificar o download

```bash
sha256sum wolfpack-academy-v0.2.0.apk
# O resultado deve ser exatamente igual ao SHA-256 na página e no arquivo SHA256SUMS.
```

A assinatura do APK pode ser inspecionada com `apksigner verify --print-certs arquivo.apk`, instalado no Android SDK Build Tools. Registrar o SHA-256 do certificado no próximo release note para que testadores possam conferir a continuidade da assinatura entre versões.

**Migração importante:** instalar o APK release sobre o APK debug poderá falhar por assinaturas divergentes. Não desinstale uma versão com progresso importante sem backup: dados locais costumam ser apagados na desinstalação.

## 5. Android Developer Console (sem taxa) · distribuição limitada

- A modalidade **Limited distribution** é diferente da Play Console e permite distribuir para até **20 dispositivos autorizados** sem taxa; está destinada a pessoa física/hobbyist, não conta de organização.
- Criar a conta em https://developer.android.com/developer-verification/guides/limited-distribution e escolher distribuição limitada.
- Registrar o identificador de pacote atual, provisoriamente `dev.wolfpackworkshop.wolfpack_academy`, provando posse pela assinatura do APK.
- Seguir a autorização de cada dispositivo por convite/QR code/link dentro do fluxo oficial da ferramenta.
- Nunca transferir a chave de assinatura privada aos testadores. Eles recebem apenas o APK final pelo portal oficial.

A verificação é um **processo operado pelo titular da conta Google**. O workflow GitHub não cadastra dispositivos nem substitui a verificação. O processo avançado de sideload de apps não verificados também existe, mas tem salvaguardas extras.

Documentação: https://developer.android.com/developer-verification/guides

## 6. F-Droid: preparação para análise, não publicação realizada

- [ ] Decidir uma **licença FLOSS explícita** para o aplicativo e seu conteúdo, com autorização do titular dos direitos.
- [ ] Definir licença dos recursos visuais (personagens/mascotes) de modo compatível com redistribuição.
- [ ] Conferir dependências e se todas são abertas, sem SDK proprietário, publicidade, telemetria oculta ou serviços não livres.
- [ ] Garantir builds do aplicativo a partir de código publicado e guia de compilação repetível.
- [ ] Incluir ícone, capturas reais de tela, descrição e política de privacidade.
- [ ] Concluir testes e demonstrar utilidade real; F-Droid pode exigir histórico mínimo de manutenção ou prova de usuários.
- [ ] Considerar F-Droid Reproducible Builds para conservar assinatura própria após validação por rebuild.
- [ ] Submeter metadata ao `fdroiddata` somente depois de atingir os critérios.

Fontes oficiais:
- https://f-droid.org/docs/Inclusion_Policy/
- https://f-droid.org/docs/Submitting_to_F-Droid_Quick_Start_Guide/
- https://f-droid.org/docs/Reproducible_Builds/

**Não aplicar uma licença ao monorepo inteiro por conveniência.** O repositório contém projetos distintos e propriedade intelectual de terceiros pode estar presente. É preciso uma decisão consciente sobre licença do app e conteúdos.

## 7. Próximos gates

- [ ] Confirmar build real de release com assinatura definitiva.
- [ ] Testar instalação limpa, uso offline, progresso, permissões e compatibilidade de Android físico.
- [ ] Publicar política de privacidade, declaração de dados e instruções claras para público-alvo (incluindo menores se aplicável).
- [ ] Publicar release e verificar que página mostra link e SHA256 corretos.
- [ ] Fazer cadastro gratuito de distribuição limitada e convidar testadores.
- [ ] Planejar publicação F-Droid após licença e auditoria.
