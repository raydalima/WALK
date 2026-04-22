#!/usr/bin/env bash

# format_project.sh
# Executa ferramentas de formatação (isort, black) se instaladas no ambiente virtual.
# Uso: ./tools/format_project.sh

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Iniciando formatação do projeto em: $ROOT_DIR"

if command -v isort >/dev/null 2>&1; then
  echo "Executando isort..."
  isort .
else
  echo "isort não encontrado; pulei isort. Instale com: pip install isort"
fi

if command -v black >/dev/null 2>&1; then
  echo "Executando black..."
  black .
else
  echo "black não encontrado; pulei black. Instale com: pip install black"
fi

echo "Formatação concluída. Verifique alterações com 'git status'."
