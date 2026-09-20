"""Stockage atomique local d'un choix 2G et de ses deux contribuables."""
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
import json
import os
import tempfile
from .tax_pension_splitting_2025 import (ConjointPension2025, ChoixFractionnement2025,
    calculer_fractionnement_2025, valider_choix_fractionnement_2025)


def sauvegarder_fractionnement_2025(profil, destination):
    valider_choix_fractionnement_2025(profil,confirmation_requise=False)
    if profil.choix_conjoint_confirme:calculer_fractionnement_2025(profil)
    p=Path(destination)
    contenu={'schema_fractionnement':1,'profil':asdict(profil)}
    p.parent.mkdir(parents=True,exist_ok=True)
    # Aucun PDF ou résultat dérivé n'est réutilisé au rechargement.
    fd,tmp=tempfile.mkstemp(prefix='.fractionnement-',suffix='.json',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(contenu,f,ensure_ascii=False,indent=2,default=str)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return p


def charger_fractionnement_2025(source):
    try:
        contenu=json.loads(Path(source).read_text(encoding='utf-8'))
        if (not isinstance(contenu,dict) or type(contenu.get('schema_fractionnement')) is not int
                or contenu['schema_fractionnement']!=1):
            raise ValueError('Format dossier de couple inconnu; les dossiers individuels restent séparés.')
        brut=contenu['profil']
        if not isinstance(brut,dict):raise ValueError('Profil invalide.')
        brut=dict(brut)
        for role in ('cedant','beneficiaire'):
            personne=dict(brut[role])
            for k in ('t4a_016','rl2_a','t4a_022','rl2_j'):
                if not isinstance(personne[k],str):raise ValueError('Montant JSON doit être une chaîne décimale.')
                personne[k]=Decimal(personne[k])
            brut[role]=ConjointPension2025(**personne)
        for k in ('montant_federal','montant_quebec','montant_361_cedant'):
            if not isinstance(brut[k],str):raise ValueError('Montant JSON invalide.')
            brut[k]=Decimal(brut[k])
        profil=ChoixFractionnement2025(**brut)
        valider_choix_fractionnement_2025(profil,confirmation_requise=False)
        if profil.choix_conjoint_confirme:calculer_fractionnement_2025(profil)
        return profil
    except (KeyError,TypeError,InvalidOperation) as e:
        raise ValueError('Dossier de couple incomplet ou mal typé.') from e
