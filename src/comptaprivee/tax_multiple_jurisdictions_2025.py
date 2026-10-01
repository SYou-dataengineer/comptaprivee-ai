"""7G : faits interprovinciaux seulement, aucun calcul T2203/TP-22.

Sources applicables à 2025 : T2203 F (25), ARC 44000; RQ 401 et 446.
La ventilation commerciale n'est jamais assimilée au pourcentage TP-22.
"""
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation

ZERO = Decimal('0')
PROVINCES_7G = {
    'AB': 'Alberta', 'BC': 'Colombie-Britannique', 'MB': 'Manitoba',
    'NB': 'Nouveau-Brunswick', 'NL': 'Terre-Neuve-et-Labrador',
    'NS': 'Nouvelle-Écosse', 'NT': 'Territoires du Nord-Ouest',
    'NU': 'Nunavut', 'ON': 'Ontario', 'PE': 'Île-du-Prince-Édouard',
    'SK': 'Saskatchewan', 'YT': 'Yukon',
}
MESSAGE_7G = ('Profil interprovincial détecté — T2203 / TP-22 requis. '
    'ComptaPrivée AI prépare les faits et les contrôles, mais ne calcule pas '
    'automatiquement l’impôt interprovincial dans ce périmètre.')
CONFIRMATIONS_7G = {
    'residence_quebec_annee': 'Résident du Québec et du Canada toute l’année 2025; aucune résidence partielle ou réputée',
    'principal_quebec': 'Établissement principal au Québec',
    'etablissement_confirme': 'Présence ou absence hors Québec vérifiée; au plus un établissement stable dans une autre province ou territoire',
    'ventilation_confirmee': 'Répartition exhaustive du revenu net vérifiée; méthode et pièces documentées, aucun double compte',
    'sans_exclusions': 'Sans immigration/émigration, décès/faillite, entreprise étrangère, société de personnes ou emploi interprovincial complexe',
    'valide_par_comptable': 'Faits, qualification de l’établissement et limites du logiciel validés par le comptable',
}


@dataclass(frozen=True)
class Administrations2025:
    reference_entreprise: str = ''
    etablissement_hors_quebec: bool = False
    province: str = ''
    revenu_quebec: Decimal = ZERO
    revenu_hors_quebec: Decimal = ZERO
    methode: str = ''
    source: str = ''
    residence_quebec_annee: bool = False
    principal_quebec: bool = False
    etablissement_confirme: bool = False
    ventilation_confirmee: bool = False
    sans_exclusions: bool = False
    valide_par_comptable: bool = False


def valider_administrations_2025(p, *, reference=None, revenu_net=None):
    if p is None:
        return None
    if type(p) is not Administrations2025:
        raise ValueError('7G : profil immuable unique requis.')
    for nom in ('reference_entreprise', 'methode', 'source'):
        if not isinstance(getattr(p, nom), str) or not getattr(p, nom).strip():
            raise ValueError('7G : répartition documentée obligatoire : ' + nom)
    if type(p.etablissement_hors_quebec) is not bool:
        raise ValueError('7G : présence hors Québec booléenne requise.')
    for nom, texte in CONFIRMATIONS_7G.items():
        if getattr(p, nom) is not True:
            raise ValueError('7G : confirmation obligatoire : ' + texte)
    if not isinstance(p.province, str):
        raise ValueError('7G : province inconnue.')
    if p.etablissement_hors_quebec:
        if p.province not in PROVINCES_7G:
            raise ValueError('7G : province inconnue; une seule province/territoire canadien hors Québec requis.')
    elif p.province or p.revenu_hors_quebec:
        raise ValueError('7G : présence hors Québec incohérente avec la juridiction ou le revenu.')
    for nom in ('revenu_quebec', 'revenu_hors_quebec'):
        v = getattr(p, nom)
        if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal('999999999.99')
                or v != v.quantize(Decimal('.01'))):
            raise ValueError('7G : montant Decimal fini non négatif au cent requis : ' + nom)
    if reference is not None and p.reference_entreprise != reference:
        raise ValueError('7G : référence différente de la fiche entreprise.')
    if revenu_net is not None and p.revenu_quebec + p.revenu_hors_quebec != revenu_net:
        raise ValueError('7G : ventilation différente du revenu net de l’entreprise; répartition exhaustive requise.')
    return p


def administrations_vers_json(p):
    if p is None:
        return None
    valider_administrations_2025(p)
    return {f.name: str(getattr(p, f.name)) if isinstance(getattr(p, f.name), Decimal)
            else getattr(p, f.name) for f in fields(p)}


def administrations_depuis_json(v):
    if v is None:
        return None
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(Administrations2025)}:
        raise ValueError('7G : champs JSON inconnus; aucun abattement, impôt ou pourcentage TP-22 manuel accepté.')
    d = dict(v)
    for nom in ('revenu_quebec', 'revenu_hors_quebec'):
        if nom not in d or not isinstance(d[nom], str):
            raise ValueError('7G : montants JSON explicites en chaînes décimales requis.')
        try:
            d[nom] = Decimal(d[nom])
        except InvalidOperation as exc:
            raise ValueError('7G : montant JSON invalide.') from exc
    return valider_administrations_2025(Administrations2025(**d))


@dataclass(frozen=True)
class PreparationAdministrations2025:
    client: str
    faits: Administrations2025
    revenu_total: Decimal
    pourcentage_quebec: Decimal | None
    pourcentage_hors_quebec: Decimal | None
    t2203_requis: bool
    tp22_requis: bool
    estimation_suspendue: bool


def preparer_administrations_2025(dossier):
    from .tax_self_employment_2025 import calculer_entreprises_2025
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in ('québec', 'quebec'):
        raise ValueError('7G : résident Québec 2025 uniquement.')
    if len(dossier.entreprises) != 1:
        raise ValueError('7G : une seule entreprise et au plus deux établissements; combinaison complexe non modélisée.')
    if dossier.documents or dossier.donnees_validees or dossier.biens_locatifs:
        raise ValueError('7G : préparation autonome seule; emploi, autres feuillets et location non modélisés ensemble.')
    resultats = calculer_entreprises_2025(dossier.entreprises)
    r = resultats[0]
    p = r.faits.administrations
    if p is None:
        raise ValueError('7G : profil de répartition absent.')
    valider_administrations_2025(p, reference=r.faits.reference, revenu_net=r.revenu_net)
    qc = p.revenu_quebec * Decimal('100') / r.revenu_net if r.revenu_net else None
    # Complément exact : pas de fuite d'arrondi d'affichage dans les montants.
    hors = Decimal('100') - qc if qc is not None else None
    return PreparationAdministrations2025(dossier.client, p, r.revenu_net, qc, hors,
        p.etablissement_hors_quebec, p.etablissement_hors_quebec, p.etablissement_hors_quebec)


def profil_interprovincial_present(dossier):
    """Détection conservatrice même avant validation des autres champs."""
    from .tax_self_employment_2025 import Entreprise2025
    if not isinstance(dossier.entreprises, tuple):
        raise ValueError('7B : liste immuable d’entreprises requise.')
    present = False
    for e in dossier.entreprises:
        if not isinstance(e, Entreprise2025):
            raise ValueError('7B : fiche entreprise invalide.')
        p = valider_administrations_2025(e.administrations)
        present = present or (p is not None and p.etablissement_hors_quebec)
    return present


def bloquer_estimation_interprovinciale_2025(dossier):
    if profil_interprovincial_present(dossier):
        raise ValueError(MESSAGE_7G)


def lignes_preparation_administrations_2025(r):
    p = r.faits
    statut = 'oui' if r.t2203_requis else 'non dans ce profil Québec seulement'
    lignes = ['ADMINISTRATIONS MULTIPLES 2025 - PRÉPARATION 7G',
        f'Client : {r.client}; entreprise : {p.reference_entreprise}',
        'Résidence Québec et Canada toute l’année; établissement principal au Québec.',
        'Juridictions : Québec' + (' et ' + PROVINCES_7G[p.province] if p.etablissement_hors_quebec else ' seulement'),
        'Établissement stable hors Québec confirmé : ' + ('oui' if p.etablissement_hors_quebec else 'absence confirmée'),
        f'Revenu net total de l’entreprise : {r.revenu_total:.2f} $',
        f'Revenu attribué au Québec : {p.revenu_quebec:.2f} $',
        f'Revenu attribué hors Québec : {p.revenu_hors_quebec:.2f} $',
        f'Contrôle : {p.revenu_quebec:.2f} + {p.revenu_hors_quebec:.2f} = {r.revenu_total:.2f} $.',
        f'Méthode de ventilation fournie : {p.methode}', f'Source documentaire : {p.source}',
        'Répartition et qualification de l’établissement confirmées par le comptable.']
    if r.pourcentage_quebec is None:
        lignes.append('Pourcentages non définis : revenu net total nul; aucune répartition inventée.')
    else:
        lignes.append(f'Répartition descriptive : Québec {r.pourcentage_quebec:.4f} %; hors Québec {r.pourcentage_hors_quebec:.4f} %.')
    lignes += ['Ces proportions descriptives ne sont pas le pourcentage fiscal TP-22.',
        'T2203 requis : ' + statut, 'TP-22 requis : ' + statut]
    if r.estimation_suspendue:
        lignes += [MESSAGE_7G, 'CALCUL ANNUEL SUSPENDU - À PRÉPARER HORS DU MOTEUR ACTUEL.',
            '42800 : calcul provincial/territorial hors moteur. Déclaration Québec conservée.',
            '44000 : aucun abattement calculé; le taux standard 16,5 % n’est pas appliqué.',
            'Impôt Québec : TP-22 à préparer; aucun ajustement estimé.',
            'FSS 446 : montant non calculé; aucune multiplication par la ventilation commerciale.',
            'La règle RQ vise annexe F ligne 82 et TP-22 ligne 35; aucun de ces calculs interprovinciaux n’est automatisé.',
            'Aucune estimation approximative, aucun remboursement ou solde annuel produit.']
    else:
        lignes.append('Aucun blocage interprovincial; les validations historiques 7B/7C restent obligatoires.')
    lignes += ['Sources : T2203 F (25); ARC ligne 44000 (2025); RQ lignes 401 et 446 (2025).',
        'Aucun formulaire officiel calculé intégralement, produit ou transmis.',
        'Exclus : plusieurs entreprises/établissements complexes, étranger, société de personnes, emploi mixte,',
        'immigration/émigration, résidence partielle ou réputée, décès/faillite.']
    return tuple(lignes)
