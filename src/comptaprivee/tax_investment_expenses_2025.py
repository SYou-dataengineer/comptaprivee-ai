"""Frais de placement et annexe N, périmètre 3E documenté pour 2025."""
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import hashlib
import json
import re

from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_field_extractor import formater_montant_fiscal

ZERO = Decimal('0')
CHAMPS_FRAIS_PLACEMENT = (
    ('gestion', 'Gestion/garde payée en 2025 (CAD, zéro explicite)'),
    ('interets', 'Intérêts simples payés en 2025 (CAD, zéro explicite)'),
    ('source', 'Facture/relevé : émetteur, compte et référence unique'),
    ('paiement', 'Preuve de paiement en 2025 et ventilation des frais'),
    ('utilisation', 'Placement concerné; contrat et utilisation directe de tout emprunt'),
    ('solde_quebec', 'Solde Québec inutilisé à l’ouverture de 2025 (zéro explicite)'),
    ('demande_252', 'Report Québec demandé en 2025, ligne 252 (zéro explicite)'),
    ('source_report', 'Annexes N, avis et historique des utilisations (si solde positif)'),
)


@dataclass(frozen=True)
class ProfilFraisPlacement2025:
    gestion: str = '0'
    interets: str = '0'
    source: str = ''
    paiement: str = ''
    utilisation: str = ''
    solde_quebec: str = '0'
    demande_252: str = '0'
    source_report: str = ''
    confirme: bool = False
    report_confirme: bool = False
    devise: str = 'CAD'
    cas_exclu: bool = False
    empreinte: str = ''


@dataclass(frozen=True)
class FraisPlacement2025:
    present: bool = False
    ligne_22100: Decimal = ZERO
    ligne_231: Decimal = ZERO
    revenus_n36: Decimal = ZERO
    ligne_260: Decimal = ZERO
    ligne_276: Decimal = ZERO
    solde_ouverture: Decimal = ZERO
    ligne_252: Decimal = ZERO
    solde_cloture: Decimal = ZERO
    assiette_fss: Decimal = ZERO
    cotisation_fss: Decimal = ZERO


def montant_frais_2025(texte):
    if not isinstance(texte, str) or not re.fullmatch(r'\d{1,9}(?:[.,]\d{1,2})?', texte):
        raise ValueError('Frais/report : montant CAD non négatif au cent près requis, zéro explicite.')
    return Decimal(texte.replace(',', '.'))


def valider_profil_frais_placement_2025(p):
    if not isinstance(p, ProfilFraisPlacement2025):
        raise ValueError('Profil frais de placement invalide.')
    for nom in ('confirme', 'report_confirme', 'cas_exclu'):
        if type(getattr(p, nom)) is not bool:
            raise ValueError('Les confirmations frais/report doivent être booléennes.')
    for nom, _ in CHAMPS_FRAIS_PLACEMENT:
        if not isinstance(getattr(p, nom), str):
            raise ValueError('Les justificatifs et montants frais doivent être du texte.')
    if p.devise != 'CAD' or p.cas_exclu:
        raise ValueError('Frais étrangers, conjoints, enregistrés, mixtes ou complexes hors périmètre 3E.')
    if not isinstance(p.empreinte, str):
        raise ValueError('Empreinte de confirmation frais invalide.')
    for nom in ('gestion', 'interets', 'solde_quebec', 'demande_252'):
        montant_frais_2025(getattr(p, nom))
    if p.confirme:
        if not p.report_confirme:
            raise ValueError('Confirmez le solde Québec, même nul, et toutes ses utilisations.')
        if any(not getattr(p, n).strip() for n in ('source', 'paiement', 'utilisation')):
            raise ValueError('Justificatifs, paiement et utilisation du placement obligatoires.')
        if montant_frais_2025(p.solde_quebec) and not p.source_report.strip():
            raise ValueError('Historique indépendant du report Québec obligatoire.')
    return p


def empreinte_frais_placement_2025(p, dossier, profil_interets, profil_dividendes, profil_capital):
    """Lie la confirmation au dossier, aux revenus et aux frais, sans données externes."""
    donnees = [(str(d.document), d.type_document, d.case, str(d.valeur_validee.normalize()), d.statut)
               for d in dossier.donnees_validees]
    contenu = [dossier.client, dossier.annee_fiscale, dossier.province,
               [str(x) for x in dossier.documents], donnees,
               asdict(profil_interets), asdict(profil_dividendes), asdict(profil_capital),
               asdict(replace(p, empreinte='', confirme=False, report_confirme=False))]
    return hashlib.sha256(json.dumps(contenu, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def verifier_confirmation_frais_2025(p, dossier, profil_interets, profil_dividendes, profil_capital):
    valider_profil_frais_placement_2025(p)
    if p.confirme and p.empreinte != empreinte_frais_placement_2025(p, dossier, profil_interets, profil_dividendes, profil_capital):
        raise ValueError('Confirmation frais périmée : dossier, placement ou frais modifiés; revalidez 3E.')


def extraire_frais_placement_2025(texte):
    """Propositions locales uniquement : libellés explicites, aucune admissibilité inférée.

    Aucun cumul de pièces; doublons/absence/année ambiguë sont refusés.
    Les relevés non structurés restent à transcrire et vérifier humainement.
    """
    if not isinstance(texte, str) or set(re.findall(r'\b20\d{2}\b', texte)) != {'2025'}:
        raise ValueError('Pièce frais : année 2025 unique requise; saisie vérifiée nécessaire.')
    resultats = {}
    for nom, motif in (('gestion', r'frais de (?:gestion|garde)'), ('interets', r'int[ée]r[êe]ts (?:pay[ée]s|sur emprunt)')):
        mentions = re.findall(motif, texte, re.I)
        valeurs = re.findall(r'^[ \t]*' + motif + r'[ \t]*:[ \t]*(\d{1,9}(?:[.,]\d{1,2})?)[ \t]*(?:CAD|\$)?[ \t]*\r?$', texte, re.I | re.M)
        if mentions and (len(mentions) != 1 or len(valeurs) != 1):
            raise ValueError('Montant frais ambigu ou répété : aucune somme ni correction automatique.')
        if valeurs:
            montant_frais_2025(valeurs[0])
            resultats[nom] = valeurs[0].replace(',', '.')
    if not resultats:
        raise ValueError('Aucun montant explicitement libellé; saisie et vérification manuelles requises.')
    return resultats


def calculer_frais_placement_2025(p, revenu, interets, dividendes, capital, profil_interets):
    valider_profil_frais_placement_2025(p)
    if p == ProfilFraisPlacement2025():
        return revenu, FraisPlacement2025()
    if not p.confirme:
        raise ValueError('Confirmez les frais de placement et le report Québec 3E.')
    if sum((interets.present, dividendes.present, capital.present)) != 1:
        raise ValueError('Frais 3E : un seul parcours de placement 3A à 3D validé requis.')
    emprunt = montant_frais_2025(p.interets)
    if emprunt and (capital.present or (interets.present and profil_interets.nature == 'REMBOURSEMENT_IMPOT')):
        raise ValueError('Intérêts après vente ou liés au remboursement fiscal : hors périmètre 3E.')
    # Borne prudente avant toute déduction (IMR et frais partiellement réintégrés).
    if max(revenu.revenu_total_federal, revenu.revenu_total_quebec) + max(ZERO, capital.gain_perte) / 2 > Decimal('177882'):
        raise ValueError('Impôt minimum potentiel : revenu brut ajusté supérieur à 177 882 $, hors périmètre 3E.')
    frais = montant_frais_2025(p.gestion) + emprunt
    if frais and interets.present and profil_interets.nature == 'REMBOURSEMENT_IMPOT':
        raise ValueError('Frais associés au remboursement fiscal hors périmètre 3E; seul un report 252 documenté est permis.')
    revenus = interets.ligne_130 + dividendes.ligne_128 + capital.ligne_139
    ajustement = max(ZERO, frais - revenus)
    solde, demande = montant_frais_2025(p.solde_quebec), montant_frais_2025(p.demande_252)
    if demande > min(solde, max(ZERO, revenus - frais)):
        raise ValueError('Report 252 supérieur au solde Québec ou au surplus de revenus N36 moins N18.')
    deduction_qc = frais - ajustement + demande
    if min(revenu.revenu_net_federal, revenu.revenu_imposable_federal) < frais or min(revenu.revenu_net_quebec, revenu.revenu_imposable_quebec) < deduction_qc:
        raise ValueError('Revenu négatif/déficit nécessitant un report : hors périmètre 3E.')
    assiette = max(ZERO, interets.ligne_130 + dividendes.ligne_166 + dividendes.ligne_167 + capital.ligne_139 - frais)
    r = FraisPlacement2025(True, frais, frais, revenus, ajustement, ZERO, solde, demande,
                          solde + ajustement - demande, assiette, cotisation_fss_prestations_2025(assiette))
    return replace(revenu,
        revenu_net_federal=revenu.revenu_net_federal-frais,
        revenu_imposable_federal=revenu.revenu_imposable_federal-frais,
        revenu_net_quebec=revenu.revenu_net_quebec-deduction_qc,
        revenu_imposable_quebec=revenu.revenu_imposable_quebec-deduction_qc), r


def lignes_resume_frais_placement_2025(r, p, reports=False):
    if not r.present:
        return []
    f = formater_montant_fiscal
    return ['', 'FRAIS DE PLACEMENT 2025 — BLOC 3E',
        f'Justificatif : {p.source}; paiement : {p.paiement}',
        f'Utilisation : {p.utilisation}',
        f'Gestion/garde : {f(montant_frais_2025(p.gestion))}; intérêts : {f(montant_frais_2025(p.interets))}',
        f'Déduction fédérale 22100 / Québec 231 : {f(r.ligne_231)}',
        f'Revenus de placement N36 : {f(r.revenus_n36)}; rajustement 260 : {f(r.ligne_260)}',
        f'Rajustement 276 : {f(r.ligne_276)} ' + ('(annexe N avec pertes 3F)' if reports else '(pertes antérieures exclues)'),
        f'Report Québec : ouverture N70 {f(r.solde_ouverture)}; utilisé 252/N78 {f(r.ligne_252)}; clôture N80 {f(r.solde_cloture)}',
        f'Preuve du report : {p.source_report or "Solde nul confirmé"}',
        'Revenu total inchangé; déductions au revenu net et imposable. Aucun report fédéral de frais consommé.',
        f'FSS final 446 : {f(r.cotisation_fss)}; assiette après 231 : {f(r.assiette_fss)} (252 sans effet).',
        'Ce FSS remplace celui du parcours de placement; aucune addition des deux cotisations.',
        'Aucun frais de transaction/PBR redéduit. Pas de report rétrospectif; pertes en capital traitées séparément en 3F.']
