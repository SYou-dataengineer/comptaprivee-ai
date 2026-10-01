"""7H : déclaration finale bornée; aucune proratisation RRQ au décès.

Sources et limites : docs/moteur_fiscal_2025.md, section 7H.
Les échéances sont nominales : aucun calendrier de jours fériés n'est inventé.
"""
from dataclasses import dataclass, asdict, fields, is_dataclass
from datetime import date
from calendar import monthrange
from decimal import Decimal

MESSAGE_COMPLEXE = 'Déclaration finale complexe — traitement hors périmètre v1.0.'
MESSAGE_RRQ = ('Décès en 2025 — recalcul RRQ / remboursement ligne 452 requis. '
    'ComptaPrivée AI ne calcule pas automatiquement cette proratisation dans le périmètre v1.0.')
CONFIRMATIONS_7H = {
    'residence_confirmee': 'Résident du Canada et du Québec du 1er janvier jusqu’au décès, sans immigration/émigration.',
    'revenus_confirmes': 'Tous les revenus sont complets et attribuables à la période avant ou au jour du décès; aucun revenu reçu après le décès.',
    'actifs_confirmes': 'Aucun actif exigeant une disposition réputée, REER/FERR au décès, roulement ou choix successoral.',
    'couverture_privee': 'Couverture collective de base d’assurance médicaments pendant toute la période jusqu’au décès; aucun mois public.',
    'sans_conjoint': 'Aucun conjoint ni personne à charge; aucun conjoint exploitant une entreprise.',
    'sans_autres_credits': 'Aucune autre déduction, crédit facultatif, avance ni report IMR à réclamer ou à régulariser.',
    'valide_par_comptable': 'Date, revenus, preuve, exclusions et déclaration principale unique vérifiés par le comptable.',
}
EXCLUSIONS_7H = ('revenus_post_deces', 'actifs_complexes', 'entreprise_active',
    'conjoint_entreprise', 'declaration_distincte', 'succession', 'fiducie',
    'faillite', 'non_resident', 'interprovincial', 'cotisations_facultatives', 'report_imr')


@dataclass(frozen=True)
class Deces2025:
    date_deces: str = ''
    province: str = 'QC'
    reference_representant: str = ''
    source: str = ''
    declaration_finale: bool = True
    residence_confirmee: bool = False
    revenus_confirmes: bool = False
    actifs_confirmes: bool = False
    couverture_privee: bool = False
    sans_conjoint: bool = False
    sans_autres_credits: bool = False
    valide_par_comptable: bool = False
    revenus_post_deces: bool = False
    actifs_complexes: bool = False
    entreprise_active: bool = False
    conjoint_entreprise: bool = False
    declaration_distincte: bool = False
    succession: bool = False
    fiducie: bool = False
    faillite: bool = False
    non_resident: bool = False
    interprovincial: bool = False
    cotisations_facultatives: bool = False
    report_imr: bool = False
    rrq_standard_18_64: bool = False


def valider_deces_2025(p):
    if p is None:
        return None
    if not isinstance(p, Deces2025):
        raise ValueError('7H : profil décès invalide.')
    for n in ('date_deces', 'province', 'reference_representant', 'source'):
        if not isinstance(getattr(p, n), str) or not getattr(p, n).strip():
            raise ValueError('7H : date, province, référence et source obligatoires.')
    try:
        jour = date.fromisoformat(p.date_deces)
    except ValueError as exc:
        raise ValueError('7H : date de décès ISO YYYY-MM-DD requise.') from exc
    if jour.year != 2025 or jour.isoformat() != p.date_deces or p.province != 'QC':
        raise ValueError(MESSAGE_COMPLEXE + ' Décès Québec 2025 uniquement.')
    for n in (*CONFIRMATIONS_7H, *EXCLUSIONS_7H, 'declaration_finale', 'rrq_standard_18_64'):
        if type(getattr(p, n)) is not bool:
            raise ValueError('7H : indicateurs booléens stricts requis.')
    if not p.declaration_finale or any(getattr(p, n) for n in EXCLUSIONS_7H):
        raise ValueError(MESSAGE_COMPLEXE + ' Revenus post-décès, succession ou situation exclue déclarée.')
    if not all(getattr(p, n) for n in CONFIRMATIONS_7H):
        raise ValueError('7H : toutes les confirmations du profil borné sont requises.')
    return jour


def echeance_deces_2025(p):
    jour = valider_deces_2025(p)
    if jour is None:
        raise ValueError('7H : profil décès requis.')
    if jour.month <= 10:
        return date(2026, 4, 30)
    mois = jour.month - 6
    return date(2026, mois, min(jour.day, monthrange(2026, mois)[1]))


def deces_vers_json(p):
    valider_deces_2025(p)
    return asdict(p) if p is not None else None


def deces_depuis_json(v):
    if v is None:
        return None
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(Deces2025)}:
        raise ValueError('7H : faits JSON inconnus ou profil invalide.')
    p = Deces2025(**v)
    valider_deces_2025(p)
    return p


def verifier_dossier_deces_2025(dossier, *, annuel=False):
    p = dossier.deces
    jour = valider_deces_2025(p)
    if jour is None:
        return
    if (dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {'québec', 'quebec'}
            or dossier.entreprises or dossier.biens_locatifs or dossier.profil_cotisations_autonomes.activer
            or dossier.registre_pertes != type(dossier.registre_pertes)()):
        raise ValueError(MESSAGE_COMPLEXE + ' Entreprise, location, pertes ou résidence hors profil 7H.')
    for d in dossier.donnees_validees:
        if d.type_document not in {'T4', 'RL-1', 'T5', 'RL-3'}:
            raise ValueError(MESSAGE_COMPLEXE + ' Seuls emploi ordinaire et intérêts T5/RL-3 sont ouverts.')
        if (not isinstance(d.valeur_validee, Decimal) or not d.valeur_validee.is_finite()
                or d.valeur_validee < 0):
            raise ValueError('7H : montant validé Decimal fini et non négatif requis.')
        if d.type_document == 'T4' and d.case in {'16', '16A'} and d.valeur_validee:
            raise ValueError(MESSAGE_COMPLEXE + ' RPC exclu.')
    if not annuel:
        return
    salaries = [d for d in dossier.donnees_validees if d.type_document in {'T4', 'RL-1'}]
    if salaries:
        from .tax_engine_input_2025 import consolider_base_fiscale_emploi_2025
        from .tax_income_2025 import calculer_cotisations_attendues_2025
        b = consolider_base_fiscale_emploi_2025(dossier)
        rrq = (b.revenu_emploi_federal, b.revenu_emploi_quebec, b.gains_admissibles_rrq,
               b.rrq_base_premiere_supplementaire, b.rrq_deuxieme_supplementaire)
        if any(rrq) and jour.month != 12:
            raise ValueError(MESSAGE_RRQ)
        if any(rrq):
            if not p.rrq_standard_18_64 or b.nombre_t4 != 1 or b.nombre_rl1 != 1:
                raise ValueError(MESSAGE_RRQ)
            a = calculer_cotisations_attendues_2025(b)
            if (b.rrq_base_premiere_supplementaire != a.rrq_ba
                    or b.rrq_deuxieme_supplementaire != a.rrq_bb):
                raise ValueError(MESSAGE_RRQ)


def verifier_options_deces_2025(dossier, options):
    verifier_dossier_deces_2025(dossier, annuel=True)
    if dossier.deces is None:
        return
    for n, v in options.items():
        if n == 'dossier' or v is None:
            continue
        if n == 'profil_interets':
            if v.nature != 'T5_RL3':
                raise ValueError(MESSAGE_COMPLEXE + ' Intérêts documentés complexes exclus.')
            continue
        if is_dataclass(v):
            try:
                vide = type(v)()
            except TypeError:
                vide = None
            if v != vide:
                raise ValueError(MESSAGE_COMPLEXE + f' Crédit/déduction non ouvert au décès : {n}.')
        elif v is not False:
            raise ValueError(MESSAGE_COMPLEXE + f' Option non ouverte au décès : {n}.')


def lignes_deces_2025(dossier):
    verifier_dossier_deces_2025(dossier)
    p = dossier.deces
    if p is None:
        return ()
    echeance = echeance_deces_2025(p)
    try:
        verifier_dossier_deces_2025(dossier, annuel=True)
        rrq = 'RRQ/452 : aucun recalcul décès ouvert; contrôles du profil satisfaits.'
    except ValueError as exc:
        rrq = 'CALCUL ANNUEL SUSPENDU : ' + str(exc)
    return ('', 'DÉCLARATION FINALE PRINCIPALE 2025 — 7H',
        f'Date du décès : {p.date_deces}; résidence au décès : Québec (QC).',
        f'Période fiscale : 2025-01-01 au {p.date_deces} inclusivement.',
        f'Représentant : référence {p.reference_representant}; preuve : {p.source}.',
        f'Échéance principale nominale T1 / TP-1 : {echeance.isoformat()}.',
        'Échéance estimée : jours fériés et fins de semaine à vérifier; aucun report automatique.',
        'Impôt minimum 2025 : non appliqué (année du décès). Reports IMR antérieurs exclus.',
        'Crédits de base et emploi ordinaires uniquement; aucun prorata automatique de crédit.',
        'Assurance médicaments : couverture collective jusqu’au décès confirmée; aucun mois public.',
        rrq, 'Exclus : revenus post-décès, dispositions réputées, REER/FERR au décès, roulement, entreprise,',
        'interprovincial, déclaration distincte, succession T3/TP-646, fiducie et crédits facultatifs.',
        'Aucun revenu post-décès ni calcul successoral pris en charge. Aucune déclaration transmise.')


def verifier_resultat_deces_2025(resultat):
    """Contrôle aussi les options d'une estimation ou d'un dossier rechargé."""
    if resultat.dossier.deces is None:
        return
    from inspect import signature
    from .tax_estimation_2025 import calculer_estimation_fiscale_2025
    options = {n:getattr(resultat,n) for n in signature(calculer_estimation_fiscale_2025).parameters
               if n != 'dossier' and hasattr(resultat,n)}
    verifier_options_deces_2025(resultat.dossier, options)
