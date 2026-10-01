"""Simuler un autre compte utilisateur pour les anciennes régressions restore."""
from unittest.mock import patch
from src.comptaprivee import app_paths, backup_manager


def restaurer_dans_profil(source, *, racine):
    with patch.object(app_paths, 'USER_DATA_DIR', racine):
        return backup_manager.restaurer_sauvegarde(source, racine=racine)
