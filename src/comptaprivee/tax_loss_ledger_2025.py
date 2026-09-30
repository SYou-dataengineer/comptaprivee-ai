"""7F : registre de pertes documentées, sans reconstitution d'une déclaration.

Les capacités historiques sont des faits vérifiés après les autres utilisations.
Ce module prépare des demandes; il ne calcule ni remboursement historique ni
perte fiscale annuelle à partir d'une perte comptable. Montants nets au cent.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
from decimal import Decimal, InvalidOperation

ZERO = Decimal('0.00')
CENT = Decimal('.01')
MAXIMUM = Decimal('999999999.99')
EXCLUSIONS_7F = (
    'ABIL/PDTPE', 'agriculture', 'pêche', 'pertes restreintes',
    'société de personnes limitée', 'perte superficielle',
    'biens personnels', 'biens précieux', 'taux historique complexe',
    'décès', 'faillite', 'déduction pour gains en capital',
    'transfert admissible d’entreprise', 'IMR',
)


@dataclass(frozen=True)
class DemandePerte2025:
    sens: str
    annee_visee: int
    montant: Decimal


@dataclass(frozen=True)
class PerteNonCapital2025:
    juridiction: str
    annee_origine: int
    disponible: Decimal
    source: str
    demandes: tuple[DemandePerte2025, ...] = ()
    historique_confirme: bool = False
    exclusions_absentes: bool = False
    solde_fiscal_confirme: bool = False


@dataclass(frozen=True)
class PerteNetteCapital2025:
    juridiction: str
    annee_origine: int
    disponible: Decimal
    source: str
    demandes: tuple[DemandePerte2025, ...] = ()
    historique_confirme: bool = False
    exclusions_absentes: bool = False
    solde_fiscal_confirme: bool = False
    taux_inclusion: Decimal = Decimal('.50')


@dataclass(frozen=True)
class CapaciteReport2025:
    """Capacité résiduelle documentée, pas un revenu historique à recalculer."""
    juridiction: str
    annee_visee: int
    revenu_imposable_disponible: Decimal
    gains_imposables_disponibles: Decimal
    source: str
    autres_pertes_appliquees: bool = False
    historique_confirme: bool = False
    sans_rajustement_annexe_n: bool = False
    exclusions_absentes: bool = False


@dataclass(frozen=True)
class RegistrePertes2025:
    pertes_non_capital: tuple[PerteNonCapital2025, ...] = ()
    pertes_net_capital: tuple[PerteNetteCapital2025, ...] = ()
    capacites: tuple[CapaciteReport2025, ...] = ()


@dataclass(frozen=True)
class UtilisationPerte2025:
    nature: str
    juridiction: str
    annee_origine: int
    sens: str
    annee_visee: int
    montant: Decimal
    formulaire: str
    ligne: str
    solde_apres_demande: Decimal


@dataclass(frozen=True)
class SoldePerte7F2025:
    nature: str
    juridiction: str
    annee_origine: int
    disponible: Decimal
    demande: Decimal
    restant: Decimal
    derniere_annee_future: int | None
    source: str


@dataclass(frozen=True)
class PreparationPertes2025:
    utilisations: tuple[UtilisationPerte2025, ...] = ()
    soldes: tuple[SoldePerte7F2025, ...] = ()

    def deduction(self, nature, juridiction):
        return sum((u.montant for u in self.utilisations if u.sens == 'courant'
                    and u.nature == nature and u.juridiction == juridiction), ZERO)


def _montant(v, nom):
    if (not isinstance(v, Decimal) or not v.is_finite()
            or not ZERO <= v <= MAXIMUM or v != v.quantize(CENT)):
        raise ValueError('7F : Decimal fini non négatif au cent requis : ' + nom)


def _juridiction(v):
    if v not in ('federal', 'quebec'):
        raise ValueError('7F : juridiction federal ou quebec requise, soldes indépendants.')


def _source(v):
    if not isinstance(v, str) or not v.strip():
        raise ValueError('7F : source documentaire obligatoire.')


def _confirmation(objet, noms):
    for nom in noms:
        if getattr(objet, nom) is not True:
            raise ValueError('7F : confirmation obligatoire : ' + nom)


def valider_registre_pertes_2025(r):
    if not isinstance(r, RegistrePertes2025):
        raise ValueError('7F : registre invalide.')
    for nom, classe, debut in (
        ('pertes_non_capital', PerteNonCapital2025, 2006),
        ('pertes_net_capital', PerteNetteCapital2025, 2004),
    ):
        pertes = getattr(r, nom)
        if not isinstance(pertes, tuple):
            raise ValueError('7F : liste immuable de pertes requise.')
        cles = set()
        for p in pertes:
            if type(p) is not classe:
                raise ValueError('7F : types de pertes strictement séparés.')
            _juridiction(p.juridiction)
            if type(p.annee_origine) is not int or not debut <= p.annee_origine <= 2025:
                raise ValueError(f'7F : origine supportée {debut} à 2025 uniquement.')
            cle = (p.juridiction, p.annee_origine)
            if cle in cles:
                raise ValueError('7F : solde annuel dupliqué; aucune addition implicite.')
            cles.add(cle)
            _montant(p.disponible, 'solde disponible')
            _source(p.source)
            _confirmation(p, ('historique_confirme', 'exclusions_absentes', 'solde_fiscal_confirme'))
            if classe is PerteNetteCapital2025:
                if (not isinstance(p.taux_inclusion, Decimal) or not p.taux_inclusion.is_finite()
                        or p.taux_inclusion != Decimal('.50')):
                    raise ValueError('7F : seuls les soldes nets déjà calculés à 50 % sont supportés.')
            if not isinstance(p.demandes, tuple):
                raise ValueError('7F : demandes immuables requises.')
            annees = set()
            total = ZERO
            for d in p.demandes:
                if type(d) is not DemandePerte2025 or type(d.annee_visee) is not int:
                    raise ValueError('7F : demande ou année invalide.')
                _montant(d.montant, 'montant demandé')
                if d.montant == ZERO:
                    raise ValueError('7F : omettez les demandes nulles; le solde futur est calculé.')
                if d.sens == 'courant':
                    if d.annee_visee != 2025 or p.annee_origine == 2025:
                        raise ValueError('7F : utilisation courante de pertes antérieures seulement.')
                elif d.sens == 'arriere':
                    if p.annee_origine != 2025 or d.annee_visee not in (2022, 2023, 2024):
                        raise ValueError('7F : report arrière de 2025 vers 2022, 2023 ou 2024 seulement.')
                else:
                    raise ValueError('7F : sens courant/arriere requis; futur = solde non consommé.')
                if d.annee_visee in annees:
                    raise ValueError('7F : demande dupliquée pour une même année.')
                annees.add(d.annee_visee)
                total += d.montant
            if total > p.disponible:
                raise ValueError('7F : demandes supérieures au solde disponible.')
    if not isinstance(r.capacites, tuple):
        raise ValueError('7F : capacités immuables requises.')
    cles = set()
    for c in r.capacites:
        if type(c) is not CapaciteReport2025:
            raise ValueError('7F : capacité historique invalide.')
        _juridiction(c.juridiction)
        if type(c.annee_visee) is not int or c.annee_visee not in (2022, 2023, 2024, 2025):
            raise ValueError('7F : capacité limitée aux années 2022 à 2025.')
        cle = (c.juridiction, c.annee_visee)
        if cle in cles:
            raise ValueError('7F : capacité annuelle dupliquée.')
        cles.add(cle)
        _montant(c.revenu_imposable_disponible, 'capacité imposable')
        _montant(c.gains_imposables_disponibles, 'capacité gains imposables')
        _source(c.source)
        _confirmation(c, ('autres_pertes_appliquees', 'historique_confirme', 'exclusions_absentes'))
        if type(c.sans_rajustement_annexe_n) is not bool:
            raise ValueError('7F : confirmation annexe N booléenne requise.')
        if c.juridiction == 'quebec' and not c.sans_rajustement_annexe_n:
            raise ValueError('7F : incidence annexe N non validée; aucun rajustement historique automatique.')
    return r


def preparer_pertes_2025(r):
    """Calcul pur, répétable : aucun solde source ni revenu historique muté."""
    valider_registre_pertes_2025(r)
    capacites = {(c.juridiction, c.annee_visee): c for c in r.capacites}
    consomme = {}
    capital_consomme = {}
    utilisations, soldes = [], []
    for nature, pertes in (('non_capital', r.pertes_non_capital), ('net_capital', r.pertes_net_capital)):
        ancien_restant = {'federal': False, 'quebec': False}
        for p in sorted(pertes, key=lambda p: (p.juridiction, p.annee_origine)):
            restant = p.disponible
            courant = any(d.sens == 'courant' for d in p.demandes)
            if courant and ancien_restant[p.juridiction]:
                raise ValueError('7F : une perte plus ancienne de même nature reste disponible.')
            for d in sorted(p.demandes, key=lambda d: d.annee_visee):
                cle = (p.juridiction, d.annee_visee)
                if cle not in capacites:
                    raise ValueError('7F : capacité documentée requise pour chaque année visée.')
                c = capacites[cle]
                consomme[cle] = consomme.get(cle, ZERO) + d.montant
                if consomme[cle] > c.revenu_imposable_disponible:
                    raise ValueError('7F : demandes combinées supérieures au revenu imposable disponible.')
                if nature == 'net_capital':
                    capital_consomme[cle] = capital_consomme.get(cle, ZERO) + d.montant
                    if capital_consomme[cle] > c.gains_imposables_disponibles:
                        raise ValueError('7F : perte nette en capital supérieure aux gains admissibles; revenu ordinaire interdit.')
                restant -= d.montant
                if d.sens == 'arriere':
                    formulaire = 'T1A 2025' if p.juridiction == 'federal' else 'TP-1012.A (2025-10)'
                    lignes = ((('66250', '66260', '66270') if nature == 'non_capital' else ('66360', '66370', '66380'))
                              if p.juridiction == 'federal' else
                              (('56', '57', '58') if nature == 'non_capital' else ('2', '3', '4')))
                    ligne = lignes[d.annee_visee - 2022]
                else:
                    formulaire = 'T1 2025' if p.juridiction == 'federal' else 'TP-1 2025'
                    ligne = ('25200' if nature == 'non_capital' else '25300') if p.juridiction == 'federal' else ('289 (289.1 = 01)' if nature == 'non_capital' else '290')
                utilisations.append(UtilisationPerte2025(nature, p.juridiction, p.annee_origine,
                    d.sens, d.annee_visee, d.montant, formulaire, ligne, restant))
            if p.annee_origine < 2025 and restant:
                ancien_restant[p.juridiction] = True
            soldes.append(SoldePerte7F2025(nature, p.juridiction, p.annee_origine,
                p.disponible, p.disponible - restant, restant,
                p.annee_origine + 20 if nature == 'non_capital' else None, p.source))
    return PreparationPertes2025(tuple(utilisations), tuple(soldes))


def registre_pertes_vers_json(r):
    valider_registre_pertes_2025(r)
    def convertir(o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, tuple):
            return [convertir(v) for v in o]
        if hasattr(o, '__dataclass_fields__'):
            return {f.name: convertir(getattr(o, f.name)) for f in fields(o)}
        return o
    return convertir(r)


def registre_pertes_depuis_json(v):
    if v is None:
        return RegistrePertes2025()
    def objet(classe, valeur, montants=()):
        if not isinstance(valeur, dict) or set(valeur) - {f.name for f in fields(classe)}:
            raise ValueError('7F : JSON ou champs non reconnus.')
        d = dict(valeur)
        for nom in montants:
            if nom not in d or not isinstance(d[nom], str):
                raise ValueError('7F : montants JSON en chaînes décimales requis.')
            try:
                d[nom] = Decimal(d[nom])
            except InvalidOperation as exc:
                raise ValueError('7F : montant JSON invalide.') from exc
        if classe in (PerteNonCapital2025, PerteNetteCapital2025):
            demandes = d.get('demandes', [])
            if not isinstance(demandes, list):
                raise ValueError('7F : liste JSON de demandes requise.')
            d['demandes'] = tuple(objet(DemandePerte2025, x, ('montant',)) for x in demandes)
        try:
            return classe(**d)
        except TypeError as exc:
            raise ValueError('7F : champs JSON obligatoires manquants.') from exc
    if not isinstance(v, dict) or set(v) - {f.name for f in fields(RegistrePertes2025)}:
        raise ValueError('7F : registre JSON invalide.')
    valeurs = {}
    for nom, classe, montants in (
        ('pertes_non_capital', PerteNonCapital2025, ('disponible',)),
        ('pertes_net_capital', PerteNetteCapital2025, ('disponible', 'taux_inclusion')),
        ('capacites', CapaciteReport2025, ('revenu_imposable_disponible', 'gains_imposables_disponibles')),
    ):
        elements = v.get(nom, [])
        if not isinstance(elements, list):
            raise ValueError('7F : liste JSON requise : ' + nom)
        valeurs[nom] = tuple(objet(classe, x, montants) for x in elements)
    r = RegistrePertes2025(**valeurs)
    return valider_registre_pertes_2025(r)


def verifier_options_pertes_2025(dossier, options):
    r = dossier.registre_pertes
    valider_registre_pertes_2025(r)
    if r == RegistrePertes2025():
        return
    for nom, valeur in options.items():
        if nom in ('dossier', 'cotisations_excedentaires', 'profil_capital') or valeur is None or valeur is False:
            continue
        if is_dataclass(valeur) and valeur == type(valeur)():
            continue
        raise ValueError('7F : combinaison non validée avec ' + nom + '; aucun double comptage avec 3F.')
    if any(p.annee_origine == 2025 for p in r.pertes_non_capital):
        raise ValueError('7F : perte non-capital 2025 externe : préparation séparée uniquement; '
                         'sa cohérence avec les revenus annuels non négatifs 7B/7D reste à établir.')


def appliquer_pertes_annuelles_2025(r, revenu, capital):
    """Capacités 2025 recalculées; aucune capacité courante saisie n'est utilisée."""
    if r == RegistrePertes2025():
        return revenu, PreparationPertes2025()
    if any(p.annee_origine == 2025 for p in r.pertes_non_capital):
        raise ValueError('7F : perte non-capital 2025 réservée à la préparation séparée.')
    for juridiction in ('federal', 'quebec'):
        courantes = [p for p in r.pertes_net_capital if p.annee_origine == 2025 and p.juridiction == juridiction]
        perte_courante = capital.perte_nette_2025
        if courantes and courantes[0].disponible != perte_courante:
            raise ValueError('7F : solde capital 2025 différent de la perte nette recalculée 3D.')
        if perte_courante and not courantes:
            raise ValueError('7F : inscrire une seule fois la perte 2025 recalculée dans chaque juridiction.')
    capacites = tuple(c for c in r.capacites if c.annee_visee != 2025) + tuple(
        CapaciteReport2025(j, 2025, getattr(revenu, 'revenu_imposable_' + j),
            capital.ligne_12700 if j == 'federal' else capital.ligne_139,
            'Moteur annuel 2025 recalculé; profils frais de placement et 3F exclus',
            True, True, True, True) for j in ('federal', 'quebec'))
    resultat = preparer_pertes_2025(replace(r, capacites=capacites))
    fed = resultat.deduction('non_capital', 'federal') + resultat.deduction('net_capital', 'federal')
    qc = resultat.deduction('non_capital', 'quebec') + resultat.deduction('net_capital', 'quebec')
    return replace(revenu, revenu_imposable_federal=revenu.revenu_imposable_federal-fed,
                   revenu_imposable_quebec=revenu.revenu_imposable_quebec-qc), resultat


def lignes_preparation_pertes_2025(r):
    p = preparer_pertes_2025(r)
    lignes = ['PERTES ET REPORTS 2025 - PRÉPARATION 7F',
        'Soldes fiscaux confirmés, distincts ARC/RQ; aucun historique reconstruit.',
        'Les demandes ne sont ni transmises ni considérées comme acceptées.',
        'Aucune ancienne déclaration, aucun revenu net historique ni crédit/prestation modifié.',
        'Aucun remboursement historique estimé. Capacités après les autres pertes déjà appliquées.']
    for u in p.utilisations:
        titre = 'Demande de report rétrospectif préparée' if u.sens == 'arriere' else 'Utilisation 2025 préparée (intégration annuelle requise)'
        lignes += [f'{titre} : {u.juridiction}, {u.nature}, origine {u.annee_origine}, année visée {u.annee_visee}.',
            f'{u.formulaire}, ligne {u.ligne} : {u.montant:.2f} $; solde après demande : {u.solde_apres_demande:.2f} $.']
    for s in p.soldes:
        limite = f'jusqu’à {s.derniere_annee_future}' if s.derniere_annee_future else 'sans limite de durée ordinaire'
        lignes += [f'{s.juridiction} / {s.nature} / {s.annee_origine} : disponible {s.disponible:.2f} $, demandé {s.demande:.2f} $, restant {s.restant:.2f} $.',
            f'Solde futur conditionnel {limite}, à rapprocher des avis. Source : {s.source}']
    lignes += ['Capital : utilisation future via 25300/T1436 et 290/TP-729; annexe N à vérifier.',
        'Non-capital : utilisation future via 25200 et 289; TP-1012.A pour le suivi Québec.',
        'Hors périmètre : ' + ', '.join(EXCLUSIONS_7F) + '.',
        'Préparation indépendante : aucun effet automatique sur la déclaration 2025.']
    return lignes


def lignes_resultat_pertes_2025(p):
    if not p.soldes:
        return []
    lignes = ['', 'PERTES ET REPORTS 2025 - 7F',
        'Déductions courantes au revenu imposable seulement; revenus nets et Québec 275 inchangés.',
        'ARC/RQ : soldes indépendants. Aucun ancien revenu net, crédit ou prestation recalculé.']
    for u in p.utilisations:
        titre = 'Demande de report rétrospectif préparée' if u.sens == 'arriere' else 'Déduction appliquée en 2025'
        lignes += [f'{titre} : {u.juridiction}, {u.nature}, origine {u.annee_origine}, année visée {u.annee_visee}.',
            f'{u.formulaire} / ligne {u.ligne} : {u.montant:.2f} $; reste après demande {u.solde_apres_demande:.2f} $.']
    for s in p.soldes:
        limite = str(s.derniere_annee_future) if s.derniere_annee_future else 'sans limite ordinaire'
        lignes += [f'{s.juridiction} / {s.nature} / {s.annee_origine} : ouverture {s.disponible:.2f} $, demandé {s.demande:.2f} $, restant {s.restant:.2f} $.',
            f'Échéance future : {limite}. Source : {s.source}']
    lignes += ['Soldes futurs conditionnels à rapprocher des avis; aucune demande transmise ou acceptée automatiquement.',
        'Report arrière distinct du solde/remboursement 2025; aucun remboursement historique calculé.',
        'Futur : 25200/289 pour non-capital; 25300/T1436 et 290/TP-729 pour capital; annexe N à vérifier.']
    return lignes
