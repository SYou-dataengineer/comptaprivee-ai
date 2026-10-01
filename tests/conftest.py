"""Isoler toutes les données applicatives des comptes utilisateur réels."""
import pytest
from src.comptaprivee import app_paths


@pytest.fixture(autouse=True)
def user_data_isole(tmp_path, monkeypatch):
    monkeypatch.setattr(app_paths, 'USER_DATA_DIR', tmp_path)
    from src.comptaprivee import tax_case_storage
    monkeypatch.setattr(tax_case_storage, 'DOSSIERS_FISCAUX_DIR', tmp_path / 'data/dossiers_fiscaux')
