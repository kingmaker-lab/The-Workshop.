#!/usr/bin/env bash
# Rodar no computador do responsável pela assinatura, nunca em Actions.
set -euo pipefail
umask 077

REPO="kingmaker-lab/The-Workshop."
KEY_DIR="$HOME/.config/wolfpack-academy"
KEY_FILE="$KEY_DIR/academy-release.p12"
KEY_ALIAS="academy"

for cmd in keytool gh base64; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Falta dependência local: $cmd" >&2
    exit 1
  fi
done

if ! gh auth status >/dev/null 2>&1; then
  echo "Faça login no GitHub CLI com 'gh auth login' antes de executar." >&2
  exit 1
fi

mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"
echo "A chave de assinatura pertence somente a este computador: $KEY_FILE"
echo "A senha NÃO será mostrada nem registrada no GitHub ou nos logs."

read -r -s -p "Senha forte da chave de release: " PASS
echo
if [ -z "$PASS" ] || [ "${#PASS}" -lt 16 ]; then
  echo "Use ao menos 16 caracteres; operação cancelada." >&2
  exit 1
fi
if [ ! -f "$KEY_FILE" ]; then
  read -r -s -p "Confirme a senha para criar a chave: " CONFIRM
  echo
  if [ "$PASS" != "$CONFIRM" ]; then
    echo "As senhas não conferem." >&2
    exit 1
  fi
  unset CONFIRM
  export WOLFPACK_RELEASE_PASSWORD="$PASS"
  keytool -genkeypair -noprompt \
    -keystore "$KEY_FILE" \
    -storetype PKCS12 \
    -keyalg RSA \
    -keysize 3072 \
    -validity 10000 \
    -alias "$KEY_ALIAS" \
    -dname "CN=Wolfpack Academy, OU=The Workshop, O=The Workshop, C=BR" \
    -storepass:env WOLFPACK_RELEASE_PASSWORD \
    -keypass:env WOLFPACK_RELEASE_PASSWORD
  chmod 600 "$KEY_FILE"
else
  export WOLFPACK_RELEASE_PASSWORD="$PASS"
  echo "Reutilizando a chave já existente. NÃO será criada outra."
fi

if ! keytool -list -keystore "$KEY_FILE" \
  -storepass:env WOLFPACK_RELEASE_PASSWORD -alias "$KEY_ALIAS" >/dev/null; then
  echo "Falha ao validar a chave existente. Os segredos NÃO foram atualizados." >&2
  exit 1
fi

echo "Enviando exclusivamente os segredos criptografados ao GitHub Actions..."
base64 -w 0 "$KEY_FILE" | gh secret set ACADEMY_KEYSTORE_B64 --repo "$REPO"
printf '%s' "$PASS" | gh secret set ACADEMY_STORE_PASSWORD --repo "$REPO"
printf '%s' "$PASS" | gh secret set ACADEMY_KEY_PASSWORD --repo "$REPO"
printf '%s' "$KEY_ALIAS" | gh secret set ACADEMY_KEY_ALIAS --repo "$REPO"

unset PASS WOLFPACK_RELEASE_PASSWORD
echo "Segredos cadastrados no repositório."
echo "IMPORTANTE: faça 2 backups criptografados da chave e guarde a senha fora deste computador."
echo "Não desinstale o beta anterior se desejar preservar o progresso local."
echo "Após validar a proteção do ambiente android-release, execute o workflow manual de release na branch main."
