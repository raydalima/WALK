#!/usr/bin/env python3
"""
Limpeza automática de arquivos/pastas desnecessários no repositório.

Use com cuidado: este script remove arquivos e diretórios correspondentes a
padrões como __pycache__, *.pyc, *~, .DS_Store, *.swp, .pytest_cache.

Execute desde a raiz do projeto:
    python3 scripts/cleanup_unnecessary.py
"""

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Padrões de arquivos e diretórios a remover
FILE_SUFFIXES = ('.pyc', '.pyo', '~', '.swp')
FILE_NAMES = ('.DS_Store',)
DIR_NAMES = ('__pycache__', '.pytest_cache', '.mypy_cache', '.cache')

removed = []
errors = []

for root, dirs, files in os.walk(PROJECT_ROOT):
    # Remover diretórios alvo
    for d in list(dirs):
        if d in DIR_NAMES:
            full = Path(root) / d
            try:
                shutil.rmtree(full)
                removed.append(str(full))
            except Exception as exc:
                errors.append((str(full), str(exc)))
            # também remover do list para evitar descer nele
            dirs.remove(d)

    # Remover arquivos por nome
    for f in files:
        full = Path(root) / f
        if f in FILE_NAMES or f.endswith(FILE_SUFFIXES):
            try:
                full.unlink()
                removed.append(str(full))
            except Exception as exc:
                errors.append((str(full), str(exc)))

# Remover top-level caches (caso não pegos pelo walk)
for dn in DIR_NAMES:
    top = PROJECT_ROOT / dn
    if top.exists() and top.is_dir():
        try:
            shutil.rmtree(top)
            removed.append(str(top))
        except Exception as exc:
            errors.append((str(top), str(exc)))

# Report
print('\nCleanup concluído.')
print(f'Total removidos: {len(removed)}')
if removed:
    for p in removed:
        print(' -', p)

if errors:
    print('\nErros ao remover alguns itens:')
    for p, e in errors:
        print(' -', p, ':', e)

sys.exit(0)
