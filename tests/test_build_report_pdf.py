"""Pruebas de la conversión del informe a PDF (scripts/build_report_pdf.py, tarea T017 de specs/004-informe-tecnico-pdf).

Solo se prueban las partes que transforman texto (separar portada, quitar la lista de comprobación, marcar figuras y
pies); la impresión con el navegador se comprueba al generar el PDF.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_report_pdf", ROOT / "scripts" / "build_report_pdf.py")
brp = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(brp)
except ModuleNotFoundError as error:  # markdown o pypdf no instalados (requirements-informe.txt)
    pytest.skip(f"Falta una librería del informe: {error}", allow_module_level=True)

SAMPLE = """# Informe

**Precio sugerido por noche**

Portada.

## 1. Caso

Texto.

![Figura](figuras/F01.png)

*Figura 1. Pie de la figura.*

---

### Lista de comprobación antes de entregar

- [ ] algo
"""


def test_split_source_separates_cover_and_drops_checklist():
    cover, body = brp.split_source(SAMPLE)
    assert cover.startswith("# Informe") and "## 1. Caso" not in cover
    assert body.lstrip().startswith("## 1. Caso")
    assert "Lista de comprobación" not in body
    assert not body.rstrip().endswith("---")


def test_to_html_marks_figures_captions_and_builds_index():
    html = brp.to_html(*brp.split_source(SAMPLE))
    assert '<p class="figure"><img' in html
    assert '<p class="caption"><em>Figura 1.' in html
    assert '<p class="subtitulo">Precio sugerido por noche</p>' in html
    assert 'class="indice"' in html and "1. Caso" in html
