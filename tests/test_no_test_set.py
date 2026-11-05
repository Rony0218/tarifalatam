"""Ningún código de src/ ni de los notebooks 04 a 06 y 08 puede leer el conjunto de prueba (se abre una vez, en la etapa 7).

Los notebooks 07 (evaluación única) y 09 (comprobar que el modelo exportado es el evaluado) solo pueden leerla con
`validation.open_test`, que deja constancia de cada lectura en reports/prueba_abierta.txt.

Se buscan los textos "test.csv" y "test.joblib" en el código, sin contar comentarios ni docstrings, que sí pueden decir
que la prueba no se abre (auditoría de fuga del 2026-10-31).
"""
import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEST_SET = re.compile(r"(?<![A-Za-z0-9_])test\.(csv|joblib)")


def _code_strings(source: str) -> list:
    """Textos del código, sin docstrings (los comentarios no llegan al árbol de sintaxis)."""
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings
    ]


def mentions_test_set(source: str) -> bool:
    return any(TEST_SET.search(text) for text in _code_strings(source))


def test_detector_finds_a_read_and_ignores_comments_and_docstrings():
    assert mentions_test_set('import pandas as pd\npd.read_csv("data/processed/test.csv.gz")')
    assert mentions_test_set('PATH = DIR / "test.joblib"')
    assert not mentions_test_set('"""La prueba (test.csv.gz) no se abre."""\nx = 1  # test.csv.gz no se lee')
    assert not mentions_test_set('PATH = "latest.csv"')


CODE_FILES = sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "app").rglob("*.py"), *(ROOT / "scripts").rglob("*.py")])


@pytest.mark.parametrize("path", CODE_FILES, ids=lambda p: p.name)
def test_src_app_and_scripts_do_not_read_the_test_set(path):
    assert not mentions_test_set(path.read_text(encoding="utf-8"))


def _code_cells(name: str) -> list:
    cells = json.loads((ROOT / "notebooks" / f"{name}.ipynb").read_text(encoding="utf-8"))["cells"]
    return ["".join(cell["source"]) for cell in cells if cell["cell_type"] == "code"]


# Otras vías a los anuncios de la prueba: abrirla, o reconstruirla desde data/raw (auditoría de fuga del 2026-11-05)
TEST_ACCESS = ("open_test", "build_unfiltered_test", "_clean_and_split")


def _calls(source: str, name: str) -> int:
    """Cuántas veces se LLAMA a una función (no cuenta comentarios, textos ni importaciones)."""
    return sum(
        1
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == name
    )


@pytest.mark.parametrize("name", ["04_features", "05_torneo", "06_optimizacion", "08_registro_modelo"])
def test_notebooks_without_test_access_do_not_read_the_test_set(name):
    for source in _code_cells(name):
        assert not mentions_test_set(source), f"{name}: una celda lee la prueba"
        for function in TEST_ACCESS:
            assert _calls(source, function) == 0, f"{name}: llama a {function}, que da acceso a la prueba"


@pytest.mark.parametrize("name, expected", [("07_validacion_interpretacion", 1), ("09_inferencia", 1)])
def test_open_test_is_called_exactly_once(name, expected):
    assert sum(_calls(source, "open_test") for source in _code_cells(name)) == expected


def test_only_notebook_07_rebuilds_the_unfiltered_test():
    for name in ["09_inferencia"]:
        assert sum(_calls(s, "build_unfiltered_test") for s in _code_cells(name)) == 0
    assert sum(_calls(s, "build_unfiltered_test") for s in _code_cells("07_validacion_interpretacion")) == 1


@pytest.mark.parametrize("name", ["07_validacion_interpretacion", "09_inferencia"])
def test_notebooks_07_and_09_read_the_test_set_only_with_open_test(name):
    for source in _code_cells(name):
        if mentions_test_set(source):
            assert "open_test(" in source, f"{name}: una celda lee la prueba sin open_test (no quedaría constancia)"
            assert "joblib.load" not in source and "read_csv" not in source, f"{name}: lee la prueba por otra vía"
