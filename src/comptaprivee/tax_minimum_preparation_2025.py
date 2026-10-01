"""7I : contrôle conservateur et préparation, sans calcul T691/TP-776.42.

Les formulaires sont requis pour examen externe, pas une affirmation d'IMR dû.
Sources 2025 et cartographie : docs/moteur_fiscal_2025.md, section 7I.
"""
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation

ZERO = Decimal('0.00')
REPERE = Decimal('177882.00')
MESSAGE_7I = ('IMR potentiel détecté — T691 ou TP-776.42 requis pour contrôle externe. '
    'ComptaPrivée AI v1.0 prépare les faits, mais ne calcule pas l’IMR. '
    'Estimation annuelle suspendue; aucun montant écrit automatiquement à 41700/40427/432.')
ELEMENTS_7I = {
    'gain_capital': 'Gain en capital intégral (annexe 3 / annexe G)',
    'perte_location': 'Perte liée à la DPA locative',
    'perte_societe': 'Perte / déduction de société de personnes ou abri fiscal',
    'cotisations': 'Cotisations syndicales / professionnelles',
    'garde': 'Frais de garde',
    'handicap': 'Déduction de soutien au handicap',
    'demenagement': 'Frais de déménagement',
    'frais_placement': 'Frais financiers / intérêts de placement',
    'rrq_rqap': 'Déductions RRQ / RPC / RQAP',
    'emploi': 'Dépenses / déductions d’emploi',
    'options': 'Options / avantages sur titres',
    'autre_preference': 'Autre préférence fiscale à examiner',
}
OPTIONS_A_EXAMINER = frozenset({
    'profil_capital', 'profil_frais_placement', 'profil_reports_pertes',
    'depenses_emploi', 'frais_garde_federaux', 'frais_demenagement',
    'autres_deductions', 'dons_bienfaisance', 'profil_dividendes',
    'profil_placement_etranger', 'fonds_travailleurs',
    'cotisations_syndicales', 'profil_credit_impot_etranger',
    'frais_garde_quebec', 'transfert_conjoint',
})


@dataclass(frozen=True)
class ElementImr2025:
    nature: str
    montant: Decimal
    source: str


@dataclass(frozen=True)
class SoldeImr2025:
    annee: int
    montant_confirme: Decimal
    source: str


@dataclass(frozen=True)
class ProfilImr2025:
    source: str = ''
    confirme: bool = False
    residence_quebec_annee: bool = False
    t691_signale: bool = False
    tp77642_signale: bool = False
    elements: tuple[ElementImr2025, ...] = ()
    soldes_federaux: tuple[SoldeImr2025, ...] = ()
    soldes_quebec: tuple[SoldeImr2025, ...] = ()


def _texte(v):
    if not isinstance(v, str) or not v.strip():
        raise ValueError('7I : source documentaire obligatoire.')


def _montant(v):
    if (not isinstance(v, Decimal) or not v.is_finite() or not ZERO <= v <= Decimal('999999999.99')
            or v != v.quantize(Decimal('.01'))):
        raise ValueError('7I : montant Decimal fini non négatif au cent requis.')


def valider_imr_2025(p):
    if p is None:
        return
    if type(p) is not ProfilImr2025:
        raise ValueError('7I : profil immuable requis.')
    _texte(p.source)
    for n in ('confirme', 'residence_quebec_annee', 't691_signale', 'tp77642_signale'):
        if type(getattr(p, n)) is not bool:
            raise ValueError('7I : confirmations booléennes requises.')
    if not p.confirme:
        raise ValueError('7I : exhaustivité des éléments, sources et soldes à confirmer.')
    if not isinstance(p.elements, tuple):
        raise ValueError('7I : liste immuable des éléments requise.')
    vus = set()
    for e in p.elements:
        if type(e) is not ElementImr2025 or e.nature not in ELEMENTS_7I or e.nature in vus:
            raise ValueError('7I : élément inconnu ou doublon; aucune saisie d’impôt final.')
        vus.add(e.nature); _montant(e.montant); _texte(e.source)
    for soldes in (p.soldes_federaux, p.soldes_quebec):
        if not isinstance(soldes, tuple):
            raise ValueError('7I : registre immuable requis.')
        annees = set()
        for s in soldes:
            if type(s) is not SoldeImr2025 or type(s.annee) is not int or not 1986 <= s.annee < 2025 or s.annee in annees:
                raise ValueError('7I : année historique invalide ou doublon dans la juridiction.')
            annees.add(s.annee); _montant(s.montant_confirme); _texte(s.source)


def imr_vers_json(p):
    valider_imr_2025(p)
    if p is None:
        return None
    return {**{n: getattr(p, n) for n in ('source', 'confirme', 'residence_quebec_annee', 't691_signale', 'tp77642_signale')},
        'elements': [dict(nature=e.nature, montant=str(e.montant), source=e.source) for e in p.elements],
        **{n: [dict(annee=s.annee, montant_confirme=str(s.montant_confirme), source=s.source)
               for s in getattr(p, n)] for n in ('soldes_federaux', 'soldes_quebec')}}


def imr_depuis_json(v):
    if v is None:
        return None
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(ProfilImr2025)}:
        raise ValueError('7I : champs JSON inconnus; impôt final manuel interdit.')
    d = dict(v)
    for n, cls, montant in (('elements', ElementImr2025, 'montant'),
            ('soldes_federaux', SoldeImr2025, 'montant_confirme'), ('soldes_quebec', SoldeImr2025, 'montant_confirme')):
        valeurs = d.get(n, [])
        if not isinstance(valeurs, list):
            raise ValueError('7I : tableau JSON requis.')
        objets = []
        for item in valeurs:
            if not isinstance(item, dict) or set(item) != {f.name for f in fields(cls)} or not isinstance(item.get(montant), str):
                raise ValueError('7I : faits JSON complets et montants décimaux en texte requis.')
            try:
                objets.append(cls(**{**item, montant: Decimal(item[montant])}))
            except (InvalidOperation, TypeError) as exc:
                raise ValueError('7I : fait JSON invalide.') from exc
        d[n] = tuple(objets)
    p = ProfilImr2025(**d); valider_imr_2025(p)
    return p


@dataclass(frozen=True)
class PreparationImr2025:
    actif: bool
    total_elements_declares: Decimal
    position_repere: str
    motifs: tuple[str, ...]
    t691_requis: bool
    tp77642_requis: bool
    deces: bool
    estimation_suspendue: bool


def preparer_imr_2025(dossier, options=None):
    p = dossier.imr
    valider_imr_2025(p)
    deces = dossier.deces is not None
    if p is None:
        return PreparationImr2025(False, ZERO, 'non évalué', (), False, False, deces, False)
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in ('québec', 'quebec'):
        raise ValueError('7I : dossier Québec 2025 requis.')
    motifs = [ELEMENTS_7I[e.nature] for e in p.elements if e.montant]
    # Le total n'inclut que des faits qualifiés fournis : ne jamais confondre
    # cotisations T4 brutes et déductions fiscales 22200/22215/22300.
    total = sum((e.montant for e in p.elements), ZERO)
    position = 'sous' if total < REPERE else 'égal' if total == REPERE else 'au-dessus'
    for d in dossier.donnees_validees:
        cases = {'T4': ('17', '17A', '44', '39', '41', '91', '92'),
                 'RL-1': ('B.A', 'B.B', 'F', 'L'), 'T5008': ('20', '21'),
                 'RL-18': ('20', '21'), 'T5': ('10', '11', '12', '15', '16', '24', '25', '26'),
                 'RL-3': ('A1', 'A2', 'B', 'C', 'F', 'G')}
        if d.type_document in cases and d.case in cases[d.type_document]:
            _montant(d.valeur_validee)
            if d.valeur_validee:
                motifs.append(f'{d.type_document} case {d.case} : qualification IMR à vérifier (non ajoutée au total déclaré)')
    if dossier.entreprises or dossier.biens_locatifs:
        motifs.append('Entreprise/location : qualification des déductions à vérifier')
    if dossier.registre_pertes != type(dossier.registre_pertes)():
        motifs.append('Pertes 7F : historique IMR distinct absent')
    for nom, v in (options or {}).items():
        if nom in OPTIONS_A_EXAMINER and v is not None and is_dataclass(v):
            try:
                present = v != type(v)()
            except TypeError:
                present = True
            if present:
                motifs.append('Profil à qualifier pour IMR : ' + nom)
    fed = bool(motifs or p.t691_signale or any(s.montant_confirme for s in p.soldes_federaux))
    qc = bool(motifs or p.tp77642_signale or any(s.montant_confirme for s in p.soldes_quebec))
    historique_deces = deces and bool(p.soldes_federaux or p.soldes_quebec)
    if deces:
        fed = qc = False
        motifs = ['Décès 7H : IMR courant non appliqué; reports antérieurs hors périmètre.']
    hors_residence = not deces and not p.residence_quebec_annee
    if hors_residence:
        motifs.append('Résidence annuelle Québec non confirmée : hors périmètre')
    return PreparationImr2025(True, total, position, tuple(dict.fromkeys(motifs)), fed, qc,
        deces, fed or qc or historique_deces or hors_residence)


def bloquer_estimation_imr_2025(dossier, options=None):
    r = preparer_imr_2025(dossier, options)
    if r.estimation_suspendue:
        if r.deces:
            raise ValueError('7H : reports IMR antérieurs exclus au décès; estimation annuelle suspendue.')
        if not dossier.imr.residence_quebec_annee:
            raise ValueError('7I : résidence annuelle Québec non confirmée; estimation annuelle suspendue.')
        raise ValueError(MESSAGE_7I)


def verifier_resultat_imr_2025(resultat):
    # Même contrôle à l'export et à la restitution, y compris objet forgé/périmé.
    bloquer_estimation_imr_2025(resultat.dossier, vars(resultat))


def lignes_imr_2025(dossier, options=None):
    r = preparer_imr_2025(dossier, options)
    if not r.actif:
        return ()
    p = dossier.imr
    lignes = ['IMR 2025 - DÉTECTION ET PRÉPARATION 7I', f'Source du contrôle : {p.source}',
        'IMR potentiel détecté : ' + ('oui' if r.t691_requis or r.tp77642_requis else 'non dans les faits examinés'),
        f'Total des éléments déclarés : {r.total_elements_declares:.2f} $; {r.position_repere} du repère 177 882 $.',
        'Indicateur seulement; total non exhaustif des calculs T691/TP-776.42. Aucun seuil universel d’exemption.',
        'T691 requis : ' + ('oui, pour contrôle externe' if r.t691_requis else 'non dans ce contrôle'),
        'TP-776.42 requis : ' + ('oui, pour contrôle externe' if r.tp77642_requis else 'non dans ce contrôle'),
        *r.motifs]
    for e in p.elements:
        lignes.append(f'{ELEMENTS_7I[e.nature]} : {e.montant:.2f} $; source : {e.source}')
    for nom, soldes in (('Fédéral', p.soldes_federaux), ('Québec', p.soldes_quebec)):
        for s in soldes:
            lignes.append(f'{nom} - solde confirmé {s.annee} : {s.montant_confirme:.2f} $; source : {s.source}')
    lignes += ['Soldes historiques : inventaire seulement; admissibilité, expiration, utilisation et reliquat non calculés.',
        'Montant non calculé par ComptaPrivée AI v1.0.',
        'Aucun montant écrit automatiquement à 41700/40427/432 au titre de l’IMR.',
        'Les lignes ordinaires existantes ne sont pas des montants IMR.',
        'CALCUL ANNUEL SUSPENDU - préparation externe requise.' if r.estimation_suspendue else
        'Aucun blocage 7I dans les faits examinés; les autres validations restent obligatoires.',
        'Sources : T691 E (25); TP-776.42 (2025-10); annexe E (2025-12).']
    return tuple(lignes)
