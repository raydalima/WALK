#!/usr/bin/env python3
from pathlib import Path
import re

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'
BACKUP_DIR = TEMPLATES_DIR.parent / 'templates_backup'

PATTERNS = [
    re.compile(r"<a[^>]*>\s*Escreva-se agora\s*</a>", re.IGNORECASE),
    re.compile(r"<button[^>]*>\s*Escreva-se agora\s*</button>", re.IGNORECASE),
]

INCLUDE_LINE = "{% include 'includes/pre_registration_cta.html' %}"


def backup_file(path: Path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dst = BACKUP_DIR / path.name
    dst.write_bytes(path.read_bytes())


def replace_in_file(path: Path):
    text = path.read_text(encoding='utf-8')
    new_text = text
    for pat in PATTERNS:
        new_text = pat.sub(INCLUDE_LINE, new_text)
    if new_text != text:
        backup_file(path)
        path.write_text(new_text, encoding='utf-8')
        print(f'Updated: {path}')


if __name__ == '__main__':
    for p in TEMPLATES_DIR.rglob('*.html'):
        if p.name == 'base.html':
            continue
        replace_in_file(p)
    print('Done.')
