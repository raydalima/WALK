import sys
from pathlib import Path

if len(sys.argv) < 3:
    print("Uso: python generate_docs_pdf.py input.md output.pdf")
    sys.exit(1)

input_md = Path(sys.argv[1])
output_pdf = Path(sys.argv[2])

if not input_md.exists():
    print(f"Arquivo de entrada não encontrado: {input_md}")
    sys.exit(1)

try:
    import markdown2
    from weasyprint import HTML
except ImportError as e:
    print("Dependência faltando:", e)
    print("Instale: pip install markdown2 weasyprint")
    sys.exit(1)

md_text = input_md.read_text(encoding='utf-8')
html = markdown2.markdown(md_text)

# Envolver em HTML básico sem usar f-string para evitar interpretação de chaves
html_doc = (
    "<!doctype html>\n"
    "<html>\n"
    "<head>\n"
    "<meta charset='utf-8'>\n"
    "<style>\n"
    "body { font-family: Arial, sans-serif; margin: 1.5cm; }\n"
    "h1, h2, h3 { color: #333; }\n"
    "code { background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }\n"
    "</style>\n"
    "</head>\n"
    "<body>\n"
    + html
    + "\n</body>\n</html>\n"
)

HTML(string=html_doc).write_pdf(str(output_pdf))
print(f"PDF gerado em: {output_pdf}")
