"""Copie explicite de l'ancien data/, sans suppression ni écrasement."""
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from . import app_paths
from .tax_case import case_id_stocke


def _sans_lien(path):
    for p in (path, *path.parents):
        if p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
            raise ValueError('Migration : lien ou jonction interdit.')


def migrer_ancien_data(ancienne_racine):
    """Appeler toutes instances fermées. Une interruption peut être reprise."""
    origine = Path(ancienne_racine)
    if not origine.is_absolute():
        raise ValueError('La racine historique doit être absolue.')
    _sans_lien(origine)
    origine = origine.resolve()
    data = origine / 'data'
    root = app_paths.user_data_dir()
    if not data.is_dir() or root == origine or root.is_relative_to(data):
        raise ValueError('Racine historique invalide.')
    fichiers = []
    for nom in ('comptaprivee.db', 'parametres.json', 'profil_comptable.json', 'ocr_review_queue.json'):
        if (data / nom).exists(): fichiers.append((data / nom, root / 'data' / nom))
    for p in sorted(data.glob('logo_societe.*')):
        if p.suffix.lower() in {'.png', '.jpg', '.jpeg'}: fichiers.append((p, root / 'data' / p.name))
    for p in sorted((data / 'dossiers_fiscaux').glob('*.json')):
        fichiers.append((p, root / 'data/dossiers_fiscaux' / p.name))
    for p in sorted((data / 'exports').rglob('*')):
        _sans_lien(p)
        if p.is_file(): fichiers.append((p, root / 'exports' / p.relative_to(data / 'exports')))
    with tempfile.TemporaryDirectory(dir=app_paths.temp_dir(), prefix='migration-') as td:
        plan = []
        for index, (source, cible) in enumerate(fichiers):
            _sans_lien(source); _sans_lien(cible)
            if not source.is_file(): raise ValueError('Source de migration non régulière.')
            copie = Path(td) / str(index)
            if source.name == 'comptaprivee.db':
                if any(Path(str(source) + s).exists() for s in ('-wal', '-shm', '-journal')):
                    raise ValueError('Fermez les accès SQLite avant migration.')
                with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as db:
                    if db.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                        raise ValueError('Base historique invalide.')
                    with closing(sqlite3.connect(copie)) as dst: db.backup(dst)
            elif source.parent.name == 'dossiers_fiscaux':
                contenu = json.loads(source.read_text(encoding='utf-8'))
                from .tax_case_storage import dossier_fiscal_depuis_contenu
                dossier_fiscal_depuis_contenu(contenu, chemin=source, verifier_documents=False)
                # La source reste intacte. La copie rend explicites les anciennes
                # références relatives et l'identité des JSON sans case_id.
                def absolu(valeur):
                    p = Path(valeur)
                    return str(p if p.is_absolute() else origine / p)
                contenu['case_id'] = case_id_stocke(contenu, source)
                contenu['documents'] = [absolu(v) for v in contenu['documents']]
                for champ in contenu['donnees_validees']: champ['document'] = absolu(champ['document'])
                if contenu.get('rapport_pdf'): contenu['rapport_pdf'] = absolu(contenu['rapport_pdf'])
                copie.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding='utf-8')
            elif source.name == 'profil_comptable.json':
                contenu = json.loads(source.read_text(encoding='utf-8'))
                if not isinstance(contenu, dict): raise ValueError('Profil historique invalide.')
                if contenu.get('logo_path') and not Path(contenu['logo_path']).is_absolute():
                    contenu['logo_path'] = str(origine / contenu['logo_path'])
                copie.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding='utf-8')
            else:
                shutil.copyfile(source, copie)
            if cible.exists():
                if not cible.is_file() or cible.read_bytes() != copie.read_bytes():
                    raise ValueError('Conflit de migration : destination différente. Résolution manuelle requise.')
            else:
                plan.append((copie, cible))
        # Tous les conflits sont examinés avant copie des données.
        for copie, cible in plan:
            _sans_lien(cible)
            cible.parent.mkdir(parents=True, exist_ok=True)
            # Lien atomique exclusif : ne remplace jamais une cible apparue depuis
            # la vérification. Staging et cible sont sur le volume utilisateur.
            os.link(copie, cible)
        app_paths.logs_dir().mkdir(parents=True, exist_ok=True)
        with (app_paths.logs_dir() / 'migration.log').open('a', encoding='utf-8') as log:
            log.write(f'migration terminee; fichiers_copies={len(plan)}\n')
    return len(plan)
