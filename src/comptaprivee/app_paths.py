"""Emplacements applicatifs, indépendants du répertoire de lancement."""
import os
import sys
from pathlib import Path

PROGRAM_DIR = (Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False)
               else Path(__file__).resolve().parents[2])
RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', PROGRAM_DIR)).resolve()


def _user_root():
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA')
        if not base or not Path(base).is_absolute():
            raise RuntimeError('LOCALAPPDATA doit désigner un dossier utilisateur absolu.')
        return Path(base) / 'ComptaPriveeAI'
    base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    if not base.is_absolute():
        raise RuntimeError('XDG_DATA_HOME doit être absolu.')
    return base / 'ComptaPriveeAI'


USER_DATA_DIR = _user_root()


def user_data_dir():
    root = Path(USER_DATA_DIR).resolve()
    if root.is_relative_to(PROGRAM_DIR.resolve()) or root.is_relative_to(RESOURCE_DIR.resolve()):
        raise ValueError('Les données utilisateur doivent rester hors du programme.')
    return root


def resource_path(relative):
    path = (RESOURCE_DIR / relative).resolve()
    if not path.is_relative_to(RESOURCE_DIR):
        raise ValueError('Ressource hors du programme.')
    return path


def database_path(): return user_data_dir() / 'data/comptaprivee.db'
def tax_cases_dir(): return user_data_dir() / 'data/dossiers_fiscaux'
def settings_path(): return user_data_dir() / 'data/parametres.json'
def accounting_profile_path(): return user_data_dir() / 'data/profil_comptable.json'
def ocr_queue_path(): return user_data_dir() / 'data/ocr_review_queue.json'
def ocr_data_dir(): return user_data_dir() / 'data/ocr'
def exports_dir(): return user_data_dir() / 'exports'
def logs_dir(): return user_data_dir() / 'logs'
def temp_dir():
    path = user_data_dir() / 'temp'
    path.mkdir(parents=True, exist_ok=True)
    return path


def backup_temp_dir(destination):
    """Staging sur le volume de destination, sans utiliser le cwd."""
    path = Path(destination).resolve().parent
    if path.is_relative_to(PROGRAM_DIR.resolve()) or path.is_relative_to(RESOURCE_DIR.resolve()):
        raise ValueError('Sauvegarde interdite dans le programme.')
    path.mkdir(parents=True, exist_ok=True)
    return path
