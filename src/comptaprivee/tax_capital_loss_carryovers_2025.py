"""3F : pertes ordinaires 2004–2024 à 50 %, soldes distincts et annexe N 2025."""
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import hashlib
import json
import re

from .tax_investment_expenses_2025 import montant_frais_2025
from .tax_field_extractor import formater_montant_fiscal

ZERO = Decimal('0')
CHAMPS_REPORTS_PERTES = (
    ('historique', 'Soldes nets : année; fédéral; Québec (lignes séparées par |, vide si aucun)'),
    ('source_federale', 'Avis ARC, annexes 3 et registre exhaustif des utilisations'),
    ('source_quebec', 'Avis RQ, annexes G, TP-729 et registre exhaustif des utilisations'),
    ('demande_federale', 'Demande 2025 fédérale 25300 (CAD, zéro explicite)'),
    ('demande_quebec', 'Demande 2025 Québec 290 (CAD, zéro explicite)'),
)


@dataclass(frozen=True)
class ProfilReportsPertes2025:
    historique: str = ''
    source_federale: str = ''
    source_quebec: str = ''
    demande_federale: str = '0'
    demande_quebec: str = '0'
    historique_confirme: bool = False
    confirme: bool = False
    retrospectif: bool = False
    cas_exclu: bool = False
    empreinte: str = ''


@dataclass(frozen=True)
class SoldePerte2025:
    annee: int
    ouverture_federale: Decimal
    ouverture_quebec: Decimal
    utilise_federal: Decimal = ZERO
    utilise_quebec: Decimal = ZERO
    cloture_federale: Decimal = ZERO
    cloture_quebec: Decimal = ZERO


@dataclass(frozen=True)
class ReportsPertes2025:
    present: bool = False
    ligne_25300: Decimal = ZERO
    ligne_290: Decimal = ZERO
    ligne_276: Decimal = ZERO
    perte_2025: Decimal = ZERO
    soldes: tuple[SoldePerte2025, ...] = ()


def lire_historique_pertes_2025(texte):
    if not isinstance(texte, str):
        raise ValueError('Historique des pertes : texte requis.')
    if not texte.strip():
        return ()
    lignes = []
    for ligne in re.split(r'[|\n]', texte):
        morceaux = [m.strip() for m in ligne.split(';')]
        if len(morceaux) != 3 or not re.fullmatch(r'20\d{2}', morceaux[0]):
            raise ValueError('Historique : année; solde net fédéral; solde net Québec requis.')
        annee = int(morceaux[0])
        if not 2004 <= annee <= 2024:
            raise ValueError('Seules les pertes ordinaires 2004 à 2024 au taux 50 % sont couvertes.')
        fed, qc = (montant_frais_2025(v) for v in morceaux[1:])
        if annee in {r.annee for r in lignes}:
            raise ValueError('Année de perte dupliquée; aucune addition implicite.')
        lignes.append(SoldePerte2025(annee, fed, qc, cloture_federale=fed, cloture_quebec=qc))
    return tuple(sorted(lignes, key=lambda r:r.annee))


def valider_profil_reports_pertes_2025(p):
    if not isinstance(p, ProfilReportsPertes2025):
        raise ValueError('Profil reports de pertes invalide.')
    for nom in ('historique_confirme', 'confirme', 'retrospectif', 'cas_exclu'):
        if type(getattr(p, nom)) is not bool:
            raise ValueError('Les confirmations de pertes doivent être booléennes.')
    for nom in tuple(n for n,_ in CHAMPS_REPORTS_PERTES)+('empreinte',):
        if not isinstance(getattr(p, nom), str):
            raise ValueError('Les champs reports de pertes doivent être du texte.')
    if p.retrospectif or p.cas_exclu:
        raise ValueError('Report rétrospectif, ancien taux, PDTPE, décès ou cas complexe hors périmètre 3F.')
    lire_historique_pertes_2025(p.historique)
    montant_frais_2025(p.demande_federale)
    montant_frais_2025(p.demande_quebec)
    if p.confirme and (not p.historique_confirme or not p.source_federale.strip() or not p.source_quebec.strip()):
        raise ValueError('Historique exhaustif confirmé et preuves ARC/RQ distinctes obligatoires, même si soldes nuls.')


def empreinte_reports_pertes_2025(p, dossier, capital, frais):
    valeurs = [(str(d.document), d.type_document, d.case, str(d.valeur_validee.normalize()), d.statut) for d in dossier.donnees_validees]
    contenu = [dossier.client, dossier.annee_fiscale, dossier.province,
               [str(d) for d in dossier.documents], valeurs, asdict(capital), asdict(frais),
               asdict(replace(p, empreinte='', confirme=False, historique_confirme=False))]
    return hashlib.sha256(json.dumps(contenu, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def verifier_confirmation_reports_pertes_2025(p, dossier, capital, frais):
    valider_profil_reports_pertes_2025(p)
    if p.confirme and p.empreinte != empreinte_reports_pertes_2025(p, dossier, capital, frais):
        raise ValueError('Confirmation reports de pertes périmée : dossier, capital, frais ou historique modifiés.')


def appliquer_reports_pertes_2025(p, revenu, capital, frais):
    valider_profil_reports_pertes_2025(p)
    if p == ProfilReportsPertes2025():
        return revenu, frais, ReportsPertes2025()
    if not p.confirme or not capital.present:
        raise ValueError('Reports 3F : confirmation et vente 3D validée obligatoires.')
    ouverture = lire_historique_pertes_2025(p.historique)
    fed, qc = montant_frais_2025(p.demande_federale), montant_frais_2025(p.demande_quebec)
    if fed > min(capital.ligne_12700, sum((r.ouverture_federale for r in ouverture), ZERO)):
        raise ValueError('25300 dépasse le gain imposable 12700 ou le solde fédéral.')
    if qc > min(capital.ligne_139, sum((r.ouverture_quebec for r in ouverture), ZERO)):
        raise ValueError('290 dépasse le gain imposable 139 ou le solde Québec.')
    n36 = capital.ligne_139
    rajustement = max(ZERO, qc - max(ZERO, n36 - frais.ligne_231))
    if frais.ligne_252 > max(ZERO, n36 - frais.ligne_231 - qc):
        raise ValueError('Report 252 excessif après pertes N52; revalidez la demande 3E, sans double utilisation.')
    if revenu.revenu_imposable_federal < fed or revenu.revenu_imposable_quebec < qc - rajustement:
        raise ValueError('Imposable négatif après reports : profil hors périmètre 3F.')
    reste_fed, reste_qc = fed, qc
    clotures = []
    for ligne in ouverture:
        utilise_fed, utilise_qc = min(ligne.ouverture_federale, reste_fed), min(ligne.ouverture_quebec, reste_qc)
        reste_fed -= utilise_fed
        reste_qc -= utilise_qc
        clotures.append(replace(ligne, utilise_federal=utilise_fed, utilise_quebec=utilise_qc,
            cloture_federale=ligne.ouverture_federale-utilise_fed, cloture_quebec=ligne.ouverture_quebec-utilise_qc))
    if capital.perte_nette_2025:
        clotures.append(SoldePerte2025(2025, ZERO, ZERO, cloture_federale=capital.perte_nette_2025, cloture_quebec=capital.perte_nette_2025))
    if frais.present:
        frais = replace(frais, ligne_276=rajustement, solde_cloture=frais.solde_cloture+rajustement)
    r = ReportsPertes2025(True, fed, qc, rajustement, capital.perte_nette_2025, tuple(clotures))
    return replace(revenu, revenu_imposable_federal=revenu.revenu_imposable_federal-fed,
                   revenu_imposable_quebec=revenu.revenu_imposable_quebec-qc+rajustement), frais, r


def lignes_resume_reports_pertes_2025(r, p):
    if not r.present:
        return []
    f = formater_montant_fiscal
    lignes = ['', 'REPORTS DE PERTES EN CAPITAL 2025 — BLOC 3F',
        f'Preuves fédérales : {p.source_federale}', f'Preuves Québec : {p.source_quebec}',
        f'Déductions : fédéral 25300 {f(r.ligne_25300)}; Québec 290 {f(r.ligne_290)}',
        f'Annexe N 52 : {f(r.ligne_290)}; rajustement 276 (277 = 09 si positif) : {f(r.ligne_276)}',
        'Revenus total/net, retenues et FSS inchangés; seul le revenu imposable est réduit.',
        'Soldes nets à 50 %, utilisés des plus anciens aux plus récents, séparément ARC/RQ.',
        'Registre par année : ouverture / utilisé / clôture, en dollars.']
    for s in r.soldes:
        lignes.append(f'{s.annee} — ARC : {f(s.ouverture_federale)} / {f(s.utilise_federal)} / {f(s.cloture_federale)}; Québec : {f(s.ouverture_quebec)} / {f(s.utilise_quebec)} / {f(s.cloture_quebec)}')
    lignes += [f'Perte nette 2025 ajoutée une fois aux soldes futurs : {f(r.perte_2025)}; aucun report rétrospectif.',
        'Clôtures prospectives provisoires à rapprocher des avis; solde de frais annexe N distinct.',
        'Aucun salaire réduit par une perte courante; hors soldes avant 2004, pertes spéciales, étranger, conjoint et IMR complexe.',
        'Estimation locale uniquement : aucun formulaire officiel T1A/TP-729/TP-1012.A transmis.']
    return lignes
