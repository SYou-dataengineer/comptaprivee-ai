"""7D : immeuble résidentiel unique, revenu de bien, sans DPA ni perte.

T776 F (25), p.1-2; T4036 2025, chapitre 3; TP-128 (2025-10), p.1-2.
Les exclusions ci-dessous sont des limites logicielles, non fiscales générales.
"""
from dataclasses import dataclass, fields, is_dataclass, replace
from decimal import Decimal, InvalidOperation
from .tax_rental_cca_2025 import (
    DpaLocation2025, ResultatDpaLocation2025, calculer_dpa_location_2025,
    dpa_location_vers_json, dpa_location_depuis_json, lignes_dpa_location_2025,
)

ZERO = Decimal('0')
DEPENSES_7D = {
    'publicite': 'Publicité locative (T776 8521 / TP-128 200)',
    'assurance': 'Assurance du bien, portion 2025 seulement (8690 / 210)',
    'gestion': 'Gestion locative courante, sans travaux (8871 / 216)',
    'comptabilite': 'Tenue comptable locative courante (8860 / 228)',
    'taxes_foncieres': 'Taxes municipales et scolaires courantes (9180 / 230)',
    'services_publics': 'Électricité, chauffage et eau à charge selon le bail (9220 / 238)',
}
MONTANTS_7D = ('loyers', 'autres_revenus', *DEPENSES_7D)
EXCLUSIONS_7D = {
    'dpa': 'DPA hors du profil distinct 7E',
    'capitalisable': 'Dépense capitalisable ou travaux',
    'services_entreprise': 'Services supplémentaires : repas, sécurité, nettoyage; futur profil entreprise requis',
    'copropriete': 'Copropriété ou société de personnes',
    'court_terme': 'Location à court terme, même conforme',
    'disposition': 'Disposition, récupération ou perte finale',
    'changement_usage': 'Changement d’usage ou usage personnel',
    'etranger': 'Immeuble étranger ou hors Québec',
    'terrain_vacant': 'Terrain vacant',
    'sous_valeur_marche': 'Location sous valeur marchande',
    'revenu_nature': 'Revenu en nature',
    'sinistre': 'Sinistre ou indemnité',
    'deces_faillite': 'Décès ou faillite',
}
CONFIRMATIONS_7D = {
    'residence_quebec': 'Résident Canada/Québec toute l’année 2025',
    'bien_residentiel': 'Un seul immeuble résidentiel au Québec, propriétaire unique',
    'location_annee': 'Immeuble entièrement locatif toute l’année, sans acquisition, vacance ni usage personnel',
    'revenu_bien': 'Revenu de bien, services essentiels seulement, location longue durée au prix du marché',
    'comptabilite_exercice': 'Loyers et dépenses de 2025 en comptabilité d’exercice; primes de bail acquises seulement en autres revenus',
    'depenses_admissibles': 'Charges courantes justifiées dans les deux déclarations; aucune immobilisation, restriction, taxe récupérable ou dépense hors liste',
    'sans_double_compte': 'Toutes les sources sont incluses une seule fois, sans remboursement ni montant déjà déclaré ailleurs',
    'profil_annuel': 'Location seule ou salaires ordinaires; aucun autre crédit/déduction demandé, aucun acompte; couverture médicaments privée annuelle admissible',
    'valide_par_comptable': 'Faits, sources, baux et exclusions vérifiés par le comptable',
}


@dataclass(frozen=True)
class BienLocatif2025:
    reference: str = ''
    adresse: str = ''
    debut: str = '2025-01-01'
    fin: str = '2025-12-31'
    source: str = ''
    loyers: Decimal = ZERO
    autres_revenus: Decimal = ZERO
    publicite: Decimal = ZERO
    assurance: Decimal = ZERO
    gestion: Decimal = ZERO
    comptabilite: Decimal = ZERO
    taxes_foncieres: Decimal = ZERO
    services_publics: Decimal = ZERO
    dpa: bool = False
    capitalisable: bool = False
    services_entreprise: bool = False
    copropriete: bool = False
    court_terme: bool = False
    disposition: bool = False
    changement_usage: bool = False
    etranger: bool = False
    terrain_vacant: bool = False
    sous_valeur_marche: bool = False
    revenu_nature: bool = False
    sinistre: bool = False
    deces_faillite: bool = False
    residence_quebec: bool = False
    bien_residentiel: bool = False
    location_annee: bool = False
    revenu_bien: bool = False
    comptabilite_exercice: bool = False
    depenses_admissibles: bool = False
    sans_double_compte: bool = False
    profil_annuel: bool = False
    valide_par_comptable: bool = False
    amortissement: DpaLocation2025 | None = None


@dataclass(frozen=True)
class Location2025:
    faits: BienLocatif2025 | None = None
    ligne_12599: Decimal = ZERO
    depenses: Decimal = ZERO
    ligne_12600: Decimal = ZERO
    ligne_168: Decimal = ZERO
    ligne_136: Decimal = ZERO
    cotisation_fss: Decimal = ZERO
    amortissement: ResultatDpaLocation2025 | None = None


def calculer_location_2025(biens):
    from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
    if not isinstance(biens, tuple):
        raise ValueError('7D : tuple immuable de biens requis.')
    if len(biens) > 1:
        raise ValueError('7D : doublon ou plusieurs biens; un seul immeuble supporté.')
    if not biens:
        return Location2025()
    b = biens[0]
    if not isinstance(b, BienLocatif2025):
        raise ValueError('7D : fiche locative invalide.')
    for nom in ('reference', 'adresse', 'source', 'debut', 'fin'):
        if not isinstance(getattr(b, nom), str) or not getattr(b, nom).strip():
            raise ValueError('7D : texte obligatoire : ' + nom)
    if b.debut != '2025-01-01' or b.fin != '2025-12-31':
        raise ValueError('7D : location continue du 1er janvier au 31 décembre 2025 requise; proratas exclus.')
    for nom, texte in EXCLUSIONS_7D.items():
        if type(getattr(b, nom)) is not bool or getattr(b, nom):
            raise ValueError('7D : hors périmètre logiciel : ' + texte)
    for nom, texte in CONFIRMATIONS_7D.items():
        if getattr(b, nom) is not True:
            raise ValueError('7D : confirmation obligatoire : ' + texte)
    for nom in MONTANTS_7D:
        v = getattr(b, nom)
        if (not isinstance(v, Decimal) or not v.is_finite() or v < ZERO
                or v > Decimal('999999999.99') or v != v.quantize(Decimal('.01'))):
            raise ValueError('7D : montant Decimal fini, non négatif et au cent : ' + nom)
    brut = b.loyers + b.autres_revenus
    depenses = sum((getattr(b, n) for n in DEPENSES_7D), ZERO)
    net = brut - depenses
    if net < ZERO:
        raise ValueError('7D : perte locative hors périmètre logiciel; examen des pertes requis, sans présumer leur inadmissibilité fiscale.')
    dpa = calculer_dpa_location_2025(b.amortissement, net) if b.amortissement is not None else None
    net_fed = dpa.federal.revenu_apres if dpa is not None else net
    net_qc = dpa.quebec.revenu_apres if dpa is not None else net
    return Location2025(b, brut, depenses, net_fed, brut, net_qc, cotisation_fss_prestations_2025(net_qc), dpa)


def verifier_dossier_location_2025(dossier, options=None):
    r = calculer_location_2025(dossier.biens_locatifs)
    if r.faits is None:
        return r
    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in ('québec', 'quebec'):
        raise ValueError('7D : Québec 2025 requis.')
    if dossier.entreprises or dossier.profil_cotisations_autonomes.activer:
        raise ValueError('7D : location + travail autonome 7B/7C hors périmètre; aucune modification des cotisations autonomes.')
    permis = {'T4': {'14','17','17A','18','22','24','26','55','56'},
              'RL-1': {'A','B.A','B.B','C','E','G','H','I'}}
    if any(d.type_document not in permis or (d.case not in permis[d.type_document] and d.valeur_validee)
           for d in dossier.donnees_validees):
        raise ValueError('7D : seulement des salaires ordinaires RRQ; RPC et autres revenus exclus.')
    if {p.resolve() for p in dossier.documents} != {d.document.resolve() for d in dossier.donnees_validees}:
        raise ValueError('7D : pièce non traitée; validez tous les feuillets.')
    for nom, valeur in (options or {}).items():
        if nom in ('dossier', 'cotisations_excedentaires') or valeur is None or valeur is False:
            continue
        if is_dataclass(valeur) and valeur == type(valeur)():
            continue
        raise ValueError('7D : combinaison non validée avec ' + nom + '; crédit/déduction supplémentaire hors périmètre.')
    return r


def appliquer_location_2025(revenu, location):
    if location.faits is None:
        return revenu
    return replace(revenu, **{
        f'revenu_{niveau}_{juridiction}': getattr(revenu, f'revenu_{niveau}_{juridiction}') + (location.ligne_12600 if juridiction == 'federal' else location.ligne_136)
        for niveau in ('total', 'net', 'imposable') for juridiction in ('federal', 'quebec')},
        profil='Location résidentielle simple Québec 2025 (7D)',
        limitations=(('Revenu de bien avec DPA 7E bornée; location seule ou salaire ordinaire.' if location.amortissement
                      else 'Revenu de bien sans DPA; location seule ou avec salaire ordinaire.'),))


def locations_vers_json(biens):
    calculer_location_2025(biens)
    return [{f.name: dpa_location_vers_json(b.amortissement) if f.name == 'amortissement' else
             str(getattr(b, f.name)) if f.name in MONTANTS_7D else getattr(b, f.name)
             for f in fields(b)} for b in biens]


def locations_depuis_json(v):
    if v is None:
        return ()
    if not isinstance(v, list):
        raise ValueError('7D : liste JSON de biens requise.')
    biens = []
    for brut in v:
        if not isinstance(brut, dict) or set(brut) - {f.name for f in fields(BienLocatif2025)}:
            raise ValueError('7D : fiche JSON ou champ non supporté.')
        d = dict(brut)
        d['amortissement'] = dpa_location_depuis_json(d.get('amortissement'))
        for n in MONTANTS_7D:
            if n not in d:
                raise ValueError('7D : montant JSON obligatoire manquant : ' + n)
            valeur = d[n]
            if not isinstance(valeur, str):
                raise ValueError('7D : montants JSON en chaînes décimales requis.')
            try:
                d[n] = Decimal(valeur)
            except InvalidOperation as exc:
                raise ValueError('7D : montant JSON invalide.') from exc
        biens.append(BienLocatif2025(**d))
    resultat = tuple(biens)
    calculer_location_2025(resultat)
    return resultat


def lignes_location_2025(e):
    r = e.location
    if r.faits is None:
        return ()
    b = r.faits; revenu = e.revenu; x = e.rapprochement
    lignes = ['ESTIMATION ANNUELLE LOCATION 2025 - 7D', f'Client : {e.dossier.client}',
        'Validation comptable obligatoire. Aucune déclaration transmise.',
        f'Bien : {b.reference}; adresse : {b.adresse}', f'Période : {b.debut} au {b.fin}', f'Sources : {b.source}',
        'Propriétaire unique, immeuble entièrement locatif au Québec; services essentiels seulement.',
        'Location longue durée, valeur marchande, comptabilité d’exercice confirmées.',
        'Couverture médicaments privée annuelle; aucun acompte ni crédit supplémentaire demandé.',
        '', f'Loyers T776 8141 : {b.loyers:.2f} $; autres revenus de bail 8230 : {b.autres_revenus:.2f} $',
        f'Brut T776 8299 / fédéral 12599 / TP-128 110 / Québec 168 : {r.ligne_12599:.2f} $']
    lignes += [f'{label} : {getattr(b, nom):.2f} $' for nom, label in DEPENSES_7D.items()]
    lignes += [f'Dépenses totales : {r.depenses:.2f} $']
    if r.amortissement is not None:
        lignes += lignes_dpa_location_2025(b.amortissement, r.amortissement)
    else:
        lignes += ['DPA / récupération / perte finale / part personnelle : 0.00 $']
    lignes += [f'Net = brut - dépenses - DPA fédérale; T776 9946 / fédéral 12600 : {r.ligne_12600:.2f} $',
        f'TP-128 394 / Québec 136 : {r.ligne_136:.2f} $',
        f'FSS Québec 446 (annexe F, assiette = net locatif) : {r.cotisation_fss:.2f} $',
        'Le brut est informatif; seul le NET est ajouté une fois aux revenus annuels.',
        'Le revenu de bien ne majore ni la déduction travailleur 201 ni les cotisations RRQ/RQAP.',
        '', f'Salaires fédéral / Québec : {e.base.revenu_emploi_federal:.2f} $ / {e.base.revenu_emploi_quebec:.2f} $',
        f'Revenu total fédéral : {revenu.revenu_total_federal:.2f} $',
        f'Revenu net fédéral : {revenu.revenu_net_federal:.2f} $',
        f'Revenu total Québec : {revenu.revenu_total_quebec:.2f} $',
        f'Déduction travailleur 201 : {revenu.deduction_travailleur_quebec:.2f} $',
        f'Déduction RRQ emploi 22215 / Québec 248 : {revenu.deduction_rrq_amelioree_federale:.2f} $ / {revenu.deduction_rrq_quebec:.2f} $',
        f'Base crédit RRQ emploi 30800 : {e.federal.cotisation_base_rrq:.2f} $',
        f'Revenu net Québec / ligne 275 : {revenu.revenu_net_quebec:.2f} $',
        f'Impôt fédéral après crédits et abattement : {x.impot_federal_apres_abattement:.2f} $',
        f'Impôt Québec : {e.quebec.impot_quebec_preliminaire:.2f} $',
        f'Total impôts + FSS (une fois) : {x.impot_total_preliminaire:.2f} $',
        f'Retenues : {x.retenues_totales:.2f} $',
        f'Remboursements cotisations emploi RRQ / AE / RQAP : {x.remboursement_rrq_excedentaire:.2f} $ / {x.remboursement_ae_excedentaire:.2f} $ / {x.remboursement_rqap_excedentaire:.2f} $',
        f'{x.resultat} : {max(x.solde_estime, x.remboursement_estime):.2f} $',
        'Exclusions logicielles : pertes, DPA hors profil 7E, intérêts, travaux, court terme, copropriété, autonome.',
        'Sources : T776 F (25) p.1-2; T4036 2025 ch.3; TP-128 (2025-10) p.1-2; annexe F 2025.']
    from .tax_employment_qpp_2025 import lignes_employeurs_2025
    lignes.extend(lignes_employeurs_2025(e.base, e.cotisations_excedentaires.source))
    return tuple(lignes)
