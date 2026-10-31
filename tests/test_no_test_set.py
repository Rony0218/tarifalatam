"""Ningún código de src/ ni de los notebooks 04 a 06 puede leer el conjunto de prueba (se abre una vez, en la etapa 7).

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


@pytest.mark.parametrize("path", sorted((ROOT / "src").rglob("*.py")), ids=lambda p: p.name)
def test_src_does_not_read_the_test_set(path):
    assert not mentions_test_set(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["04_features", "05_torneo", "06_optimizacion"])
def test_stage_4_to_6_notebooks_do_not_read_the_test_set(name):
    cells = json.loads((ROOT / "notebooks" / f"{name}.ipynb").read_text(encoding="utf-8"))["cells"]
    for cell in cells:
        if cell["cell_type"] == "code":
            assert not mentions_test_set("".join(cell["source"])), f"{name}: una celda lee la prueba"
