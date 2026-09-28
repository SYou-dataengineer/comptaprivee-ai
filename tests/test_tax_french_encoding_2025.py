"""Régression : préserver le français lors de l'écriture des fichiers sous Windows."""
from pathlib import Path
import ast

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("bloc", ["gui", "documentation"])
def test_bloc_5o_preserve_accents_et_symboles(bloc):
    if bloc == "documentation":
        texte = (ROOT / "docs/moteur_fiscal_2025.md").read_text(encoding="utf-8")
        section = texte[texte.index("### Bloc 5O"):].split("\n### ")[0]
        assert "Bloc 5O livré — fonds de travailleurs fédéraux" in section
    else:
        arbre = ast.parse((ROOT / "src/comptaprivee/gui.py").read_text(encoding="utf-8"))
        fonction = next(n for n in ast.walk(arbre) if isinstance(n, ast.FunctionDef)
            and n.name == "ouvrir_fonds_travailleurs_5o_2025")
        section = "\n".join(n.value for n in ast.walk(fonction)
            if isinstance(n, ast.Constant) and isinstance(n.value, str))
        assert "Prix payé ($)" in section
    # Ces textes explicatifs ne contiennent aucune question : chaque '?' serait une perte d'encodage.
    assert "?" not in section
    assert "\ufffd" not in section
