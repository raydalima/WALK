"""
Script para atualizar templates HTML no diretório templates/ para estender
templates/base.html e envolver o conteúdo existente em um bloco 'content'.

Uso:
  python scripts/update_templates_to_base.py

Observação: faça backup dos templates antes de rodar.
"""
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'

EXCLUDE = ['base.html']

for path in TEMPLATES_DIR.rglob('*.html'):
    if path.name in EXCLUDE:
        continue
    text = path.read_text(encoding='utf-8')
    if "{% extends 'base.html' %}" in text:
        continue
    # Evitar duplicar block content se já existir
    if '{% block content %}' in text:
        continue

    title = path.stem.replace('_', ' ').title()
    new_text = (
        "{% extends 'base.html' %}\n"
        "{% block title %}\n"
        + title
        + "\n{% endblock %}\n"
        "{% block content %}\n"
        + text
        + "\n{% endblock %}\n"
    )

    path.write_text(new_text, encoding='utf-8')
    print(f'Atualizado: {path}')
