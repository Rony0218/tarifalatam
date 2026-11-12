"""Convierte reports/informe_tecnico.md en reports/informe_tecnico.pdf (specs/004-informe-tecnico-pdf, tarea T017).

Uso, desde la raíz del repositorio, con el entorno activado y requirements-informe.txt instalado:

    python scripts/build_report_pdf.py

Pasos: Markdown -> HTML con estilos (portada con índice, tablas, figuras con su pie, número de página) -> PDF con
Microsoft Edge o Google Chrome en modo sin ventana. La lista de comprobación del final del .md no va al PDF.
Antes, generar las figuras con `python scripts/report_figures.py`.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import markdown
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SOURCE = REPORTS / "informe_tecnico.md"
OUTPUT = REPORTS / "informe_tecnico.pdf"
CHECKLIST_MARK = "### Lista de comprobación"
# Chrome primero: termina cuando el PDF ya está escrito. Edge devuelve el control antes y escribe después, por eso
# print_pdf espera a que aparezca el archivo.
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]
WAIT_SECONDS = 90

CSS = """
@page { size: A4; margin: 2cm 1.9cm 2cm 1.9cm;
        @bottom-center { content: counter(page); font: 9pt 'Segoe UI', Arial, sans-serif; color: #6b7280; } }
@page :first { @bottom-center { content: none; } }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10.3pt; line-height: 1.42; color: #1f2933; }
h1 { font-size: 24pt; color: #1f6f8b; margin: 0 0 4pt 0; }
h2 { font-size: 14.5pt; color: #1f6f8b; border-bottom: 1.5px solid #1f6f8b; padding-bottom: 2pt; margin: 16pt 0 6pt 0;
     break-after: avoid; }
h3 { font-size: 11.5pt; color: #174e63; margin: 11pt 0 4pt 0; break-after: avoid; }
p { margin: 4pt 0 6pt 0; }
ul, ol { margin: 3pt 0 6pt 0; padding-left: 17pt; }
li { margin-bottom: 2.5pt; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 8.8pt; background: #f1f4f7; padding: 0 2px;
       border-radius: 2px; }
a { color: #1f6f8b; text-decoration: none; }
blockquote { margin: 2pt 0 6pt 0; padding: 1pt 8pt; border-left: 3px solid #a0a7b0; color: #52606d; font-size: 9pt; }
blockquote p { margin: 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 5pt 0 8pt 0; font-size: 8.8pt; line-height: 1.3; }
th { background: #1f6f8b; color: white; text-align: left; padding: 3pt 5pt; font-weight: 600; }
td { border-bottom: 1px solid #d9dee3; padding: 2.5pt 5pt; vertical-align: top; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #f6f8fa; }
p.figure { text-align: center; margin: 6pt 0 0 0; break-inside: avoid; break-after: avoid; }
p.figure img { max-width: 100%; max-height: 9.2cm; }
p.caption { font-size: 8.8pt; color: #52606d; text-align: center; margin: 2pt 1cm 10pt 1cm; break-before: avoid; }
.portada { break-after: page; }
.portada .subtitulo { font-size: 13pt; color: #174e63; font-weight: 600; margin-bottom: 14pt; }
.portada p { font-size: 10.5pt; }
.indice { margin-top: 16pt; padding: 8pt 14pt; background: #f1f6f8; border-radius: 4px; }
.indice h2 { border: none; font-size: 12pt; margin: 2pt 0 4pt 0; }
.indice ul { list-style: none; padding-left: 0; margin: 0; columns: 2; font-size: 10pt; }
.indice ul ul { display: none; }
"""


def split_source(text: str) -> tuple[str, str]:
    """Separa la portada (todo lo anterior al primer `## `) del cuerpo, y quita la lista de comprobación final."""
    if CHECKLIST_MARK in text:
        text = text[: text.index(CHECKLIST_MARK)].rstrip()
        text = re.sub(r"\n-{3,}\s*$", "", text)  # la línea horizontal que la precedía
    first_section = text.index("\n## ")
    return text[:first_section], text[first_section:]


def to_html(cover_md: str, body_md: str) -> str:
    """HTML completo: portada con índice + cuerpo, con clases para figuras y pies de figura."""
    extensions = ["tables", "toc", "sane_lists", "attr_list"]
    body_converter = markdown.Markdown(extensions=extensions, extension_configs={"toc": {"toc_depth": "2-3"}})
    body = body_converter.convert(body_md)
    cover = markdown.markdown(cover_md, extensions=extensions)
    # La primera línea en negrita después del título es el subtítulo de la portada
    cover = re.sub(r"<p><strong>(Precio sugerido[^<]*)</strong></p>", r'<p class="subtitulo">\1</p>', cover, count=1)
    toc = f'<div class="indice"><h2>Contenido</h2>{body_converter.toc}</div>'
    body = re.sub(r"<p>(<img [^>]+>)</p>", r'<p class="figure">\1</p>', body)
    body = re.sub(r"<p><em>(Figura \d+\.)", r'<p class="caption"><em>\1', body)
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        f"<base href='{REPORTS.as_uri()}/'><title>Informe técnico — TarifaLatam</title><style>{CSS}</style></head>"
        f"<body><div class='portada'>{cover}{toc}</div>{body}</body></html>"
    )


def find_browser() -> Path:
    for path in BROWSERS:
        if path.exists():
            return path
    found = shutil.which("chrome") or shutil.which("msedge")
    if found:
        return Path(found)
    sys.exit("No encontré Google Chrome ni Microsoft Edge para imprimir el PDF.")


def _wait_for_file(path: Path, seconds: int = WAIT_SECONDS) -> bool:
    """Espera a que el archivo exista y deje de crecer (Edge lo escribe después de devolver el control)."""
    last_size = -1
    for _ in range(seconds * 2):
        if path.exists() and path.stat().st_size > 0 and path.stat().st_size == last_size:
            return True
        last_size = path.stat().st_size if path.exists() else -1
        time.sleep(0.5)
    return path.exists()


def print_pdf(html: str, output: Path) -> None:
    """Imprime el HTML a PDF con el navegador en modo sin ventana y con un perfil temporal (no toca el del usuario).

    El PDF se escribe primero en la carpeta temporal (ruta sin tildes ni espacios) y después se copia a reports/.
    """
    with tempfile.TemporaryDirectory() as tmp:
        page, pdf = Path(tmp) / "informe.html", Path(tmp) / "informe.pdf"
        page.write_text(html, encoding="utf-8")
        command = [
            str(find_browser()), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={Path(tmp) / 'perfil'}", f"--print-to-pdf={pdf}", page.as_uri(),
        ]
        subprocess.run(command, capture_output=True, timeout=180)
        if not _wait_for_file(pdf):
            sys.exit("El navegador terminó sin crear el PDF.")
        shutil.copyfile(pdf, output)


def main() -> None:
    missing = [p for p in sorted(set(re.findall(r"\]\(([^)]+\.(?:png|jpg))\)", SOURCE.read_text(encoding="utf-8"))))
               if not (REPORTS / p).exists()]
    if missing:
        sys.exit(f"Faltan figuras: {missing}. Ejecuta antes: python scripts/report_figures.py")
    cover_md, body_md = split_source(SOURCE.read_text(encoding="utf-8"))
    print_pdf(to_html(cover_md, body_md), OUTPUT)
    pages = len(PdfReader(OUTPUT).pages)
    print(f"Listo: {OUTPUT.relative_to(ROOT)} con {pages} páginas ({pages - 1} sin contar la portada)")


if __name__ == "__main__":
    main()
