#!/usr/bin/env python3
"""
format_project.py
Tenta aplicar isort e black automaticamente. Se não disponíveis, tenta
quebrar linhas longas (>= 79) como fallback (apenas heurística).
"""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception:
        return False


def run_isort_black():
    ok = False
    if shutil.which("isort"):
        print("Executando isort...")
        if run_cmd(["isort", str(ROOT)]):
            ok = True
    if shutil.which("black"):
        print("Executando black...")
        if run_cmd(["black", str(ROOT)]):
            ok = True
    return ok


def rewrap_lines(path: Path, max_len=79):
    # heurística simples: quebra comentários longos; não é perfeita
    changed = 0
    for p in path.rglob("*.py"):
        text = p.read_text(encoding="utf8")
        lines = text.splitlines()
        new_lines = []
        for ln in lines:
            if len(ln) <= max_len:
                new_lines.append(ln)
                continue
            # evitar tocar blocos complexos; tratar apenas comentários
            if ln.strip().startswith("#"):
                parts = ln.split(" ")
                cur = ""
                for w in parts:
                    if len(cur) + 1 + len(w) <= max_len:
                        cur = f"{cur} {w}".strip()
                    else:
                        new_lines.append(cur)
                        cur = w
                if cur:
                    new_lines.append(cur)
                changed += 1
            else:
                new_lines.append(ln)
        new_text = "\n".join(new_lines)
        if new_text != text:
            p.write_text(new_text, encoding="utf8")
    return changed


def main():
    print("Tentando formatar com isort/black, se disponíveis...")
    if run_isort_black():
        print("Ferramentas executadas.")
        return

    print("isort/black não disponíveis. Aplicando quebra de linhas...")
    changed = rewrap_lines(ROOT)
    print(f"Linhas reformatadas: {changed}")


if __name__ == '__main__':
    main()
