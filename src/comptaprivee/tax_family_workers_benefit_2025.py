"""Annexe 6 Québec 2025 : données familiales et calcul, hors traitements spéciaux."""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation
from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
CONFIRMATIONS_FAMILLE_ACT = {
    "situations_verifiees": "Conjoint visé au 31 décembre et admissibilités vérifiés; personnes à charge attribuées conformément à 122.7(10)",
    "revenus_verifies": "Revenus 10100/23600 et RC210 des deux personnes vérifiés; aucun revenu 10400, autonome, bourse ou ajustement PUGE/REEI omis",
    "attribution_unique": "Choix de l'ACT de base et attribution des avances convenus entre les soutiens; aucune double demande",
    "aucun_traitement_special": "Aucun décès, faillite, résidence partielle du demandeur, revenu exonéré choisi ou situation conjugale spéciale à traiter",
}


@dataclass(frozen=True)
class FamilleAllocation2025:
    activer: bool = False
    demandeur_etudiant: bool = False
    conjoint_enfant_nom: str = ""
    conjoint_enfant_naissance: str = ""
    conjoint_enfant_admissible_confirme: bool = False
    conjoint_nom: str = ""
    conjoint_resident: bool = False
    conjoint_etudiant: bool = False
    conjoint_etudiant_sans_dependant_confirme: bool = False
    conjoint_detenu: bool = False
    conjoint_exempt: bool = False
    conjoint_ciph: bool = False
    conjoint_revenu_travail: Decimal = ZERO
    conjoint_revenu_net: Decimal = ZERO
    conjoint_avances_base: Decimal = ZERO
    conjoint_reclame_base: bool = False
    enfant_nom: str = ""
    enfant_naissance: str = ""
    enfant_admissible_confirme: bool = False
    avances_base_attribuees_demandeur: bool = False
    source: str = ""
    situations_verifiees: bool = False
    revenus_verifies: bool = False
    attribution_unique: bool = False
    aucun_traitement_special: bool = False

    @property
    def conjoint_admissible(self):
        return bool(self.conjoint_nom and self.conjoint_resident and (not self.conjoint_etudiant or bool(self.conjoint_enfant_nom))
                    and not self.conjoint_detenu and not self.conjoint_exempt)


def _montant(v, nom, *, signe=False):
    if not isinstance(v, Decimal) or not v.is_finite() or (not signe and v < ZERO):
        raise ValueError("Montant familial ACT invalide : " + nom)
    try:
        if v != v.quantize(Decimal(".01")):
            raise ValueError("Montant familial ACT à exprimer en cents : " + nom)
    except InvalidOperation as exc:
        raise ValueError("Montant familial ACT hors capacité : " + nom) from exc
    return v


def valider_famille_act_2025(f):
    if not isinstance(f, FamilleAllocation2025):
        raise ValueError("Profil familial ACT invalide.")
    for champ in fields(f):
        v = getattr(f, champ.name)
        if champ.type is bool and type(v) is not bool:
            raise ValueError("Confirmation familiale ACT non booléenne : " + champ.name)
        if champ.type is str and not isinstance(v, str):
            raise ValueError("Texte familial ACT invalide : " + champ.name)
        if champ.type is Decimal:
            _montant(v, champ.name, signe=champ.name == "conjoint_revenu_net")
    if not f.activer:
        if f != FamilleAllocation2025():
            raise ValueError("Données familiales ACT présentes sans activation.")
        return f
    if not f.source.strip():
        raise ValueError("Source familiale ACT obligatoire.")
    for nom, libelle in CONFIRMATIONS_FAMILLE_ACT.items():
        if not getattr(f, nom):
            raise ValueError("Confirmation familiale ACT obligatoire : " + libelle)
    if not f.conjoint_nom.strip():
        if f.conjoint_nom or any(getattr(f, c.name) for c in fields(f)
                                if c.name.startswith("conjoint_") and c.name != "conjoint_nom"):
            raise ValueError("Données du conjoint ACT présentes sans identité.")
    for prefixe in ("enfant", "conjoint_enfant"):
        nom = getattr(f, prefixe + "_nom")
        naissance_texte = getattr(f, prefixe + "_naissance")
        confirme = getattr(f, prefixe + "_admissible_confirme")
        if nom:
            if not nom.strip() or not confirme:
                raise ValueError("Enfant ACT : identité et admissibilité confirmées obligatoires.")
            try:
                naissance = date.fromisoformat(naissance_texte)
            except ValueError as exc:
                raise ValueError("Naissance de l'enfant ACT invalide.") from exc
            if naissance.isoformat() != naissance_texte or not date(2007, 1, 1) <= naissance <= date(2025, 12, 31):
                raise ValueError("L'enfant ACT doit avoir moins de 19 ans au 31 décembre 2025.")
        elif naissance_texte or confirme:
            raise ValueError("Données de l'enfant ACT présentes sans identité.")
    normaliser = lambda n: " ".join(n.split()).casefold()
    if f.enfant_nom and normaliser(f.enfant_nom) == normaliser(f.conjoint_enfant_nom):
        raise ValueError("Un même enfant ne peut être attribué aux deux parents pour l'ACT, même avec des dates divergentes.")
    if f.conjoint_etudiant and not f.conjoint_enfant_nom and not f.conjoint_etudiant_sans_dependant_confirme:
        raise ValueError("Conjoint étudiant : confirmer l'absence de personne à charge attribuée pour lui.")
    if f.conjoint_etudiant_sans_dependant_confirme and (not f.conjoint_etudiant or f.conjoint_enfant_nom):
        raise ValueError("Confirmation du conjoint étudiant sans personne à charge contradictoire.")
    if f.conjoint_reclame_base and not f.conjoint_admissible:
        raise ValueError("Un conjoint non admissible ne peut réclamer l'ACT de base.")
    if f.conjoint_reclame_base and f.avances_base_attribuees_demandeur:
        raise ValueError("Les avances de base doivent suivre le conjoint réclamant l'ACT de base.")
    return f


@dataclass(frozen=True)
class ResultatActFamilial2025:
    travail_familial: Decimal = ZERO
    net_avant_exemption: Decimal = ZERO
    exemption_second_revenu: Decimal = ZERO
    net_familial: Decimal = ZERO
    seuil_travail: Decimal = ZERO
    taux_base: Decimal = ZERO
    plafond_base: Decimal = ZERO
    seuil_reduction_base: Decimal = ZERO
    base_avant: Decimal = ZERO
    reduction_base: Decimal = ZERO
    base: Decimal = ZERO
    taux_supplement: Decimal = ZERO
    seuil_reduction_supplement: Decimal = ZERO
    taux_reduction_supplement: Decimal = ZERO
    supplement_avant: Decimal = ZERO
    reduction_supplement: Decimal = ZERO
    supplement: Decimal = ZERO
    avances_base_retenues: Decimal = ZERO
    ligne_45300: Decimal = ZERO
    ligne_41500: Decimal = ZERO
    demandeur_admissible: bool = False
    conjoint_admissible: bool = False


def calculer_act_familial_2025(p, *, revenu_travail, revenu_net):
    f = valider_famille_act_2025(p.famille)
    travail = _montant(revenu_travail, "10100 demandeur")
    net = max(_montant(revenu_net, "23600 demandeur", signe=True), ZERO)
    if not f.activer:
        return ResultatActFamilial2025()
    if p.reclamer_base and f.conjoint_reclame_base:
        raise ValueError("Deux demandes d'ACT de base dans le couple.")
    admissible = not f.demandeur_etudiant or bool(f.enfant_nom)
    base_demandee = p.reclamer_base and admissible
    supplement_demande = p.reclamer_supplement and admissible
    conjoint, enfant = f.conjoint_admissible, bool(f.enfant_nom)
    travail_c = f.conjoint_revenu_travail if conjoint else ZERO
    net_c = max(f.conjoint_revenu_net, ZERO) if conjoint else ZERO
    exemption = (min(travail, net, Decimal(16386)) if travail < travail_c else
                 min(travail_c, net_c, Decimal(16386))) if conjoint else ZERO
    familial = net + net_c - exemption
    params = {
        (False, False): ("2400", ".373", "3812.06", "14170.05", "33230.35"),
        (True, False): ("3600", ".373", "5943.38", "21787.19", "51504.09"),
        (False, True): ("2400", ".20", "2044", "14341.56", "24561.56"),
        (True, True): ("3600", ".239", "3808.23", "22007.75", "41048.90"),
    }
    seuil, taux, plafond, seuil_base, seuil_supp = map(Decimal, params[conjoint, enfant])
    avant = min(plafond, arrondir_cent(max(travail + travail_c - seuil, ZERO) * taux)) if base_demandee else ZERO
    reduction = arrondir_cent(max(familial - seuil_base, ZERO) * Decimal(".20")) if base_demandee else ZERO
    base = max(avant - reduction, ZERO)
    taux_supp = Decimal(".20") if conjoint else Decimal(".40")
    taux_reduction_supp = Decimal(".10") if conjoint and f.conjoint_ciph else Decimal(".20")
    supp_avant = min(Decimal("851.31"), arrondir_cent(max(travail - Decimal(1200), ZERO) * taux_supp)) if supplement_demande else ZERO
    supp_reduction = arrondir_cent(max(familial - seuil_supp, ZERO) * taux_reduction_supp) if supplement_demande else ZERO
    supplement = max(supp_avant - supp_reduction, ZERO)
    avances_base = (p.avances_rc210_case10 + f.conjoint_avances_base
                    if p.reclamer_base or f.avances_base_attribuees_demandeur or not f.conjoint_nom else ZERO)
    credit = base + supplement
    return ResultatActFamilial2025(travail+travail_c, net+net_c, exemption, familial,
        seuil, taux, plafond, seuil_base, avant, reduction, base, taux_supp, seuil_supp,
        taux_reduction_supp, supp_avant, supp_reduction, supplement, avances_base, credit,
        min(credit, avances_base + p.avances_rc210_case11), admissible, conjoint)


def famille_act_vers_dict(f):
    valider_famille_act_2025(f)
    return {k: format(v, ".2f") if isinstance(v, Decimal) else v for k, v in asdict(f).items()}


def verifier_concordance_act_familial_2025(p, *, demandeur, medical, supplement,
        conjoint_30300, personne_30400, conjoint_32600=None, noms_conjoints=()):
    if not p.famille.activer:
        return
    f = p.famille
    normaliser = lambda n: " ".join(n.split()).casefold()
    if f.conjoint_nom and normaliser(f.conjoint_nom) == normaliser(demandeur):
        raise ValueError("Le conjoint ACT doit différer du demandeur.")
    if any(n and normaliser(n) in {normaliser(demandeur), normaliser(f.conjoint_nom)}
           for n in (f.enfant_nom, f.conjoint_enfant_nom)):
        raise ValueError("L'enfant ACT doit différer du demandeur et de son conjoint.")
    noms = list(noms_conjoints) + [x.nom for x in medical.personnes if x.lien == "conjoint"]
    if conjoint_32600 is not None:
        noms.append(conjoint_32600.nom_conjoint)
    if any(n and normaliser(n) != normaliser(f.conjoint_nom) for n in noms):
        raise ValueError("Identité du conjoint ACT divergente entre profils.")
    if conjoint_30300.reclamer_montant or conjoint_32600 is not None:
        if not f.conjoint_nom or not f.conjoint_resident:
            raise ValueError("Les profils 30300/32600 exigent un conjoint résident du Canada toute l'année.")
        revenus = ([conjoint_30300.revenu_net_conjoint_2025] if conjoint_30300.reclamer_montant else [])
        if conjoint_32600 is not None:
            revenus.append(conjoint_32600.revenu_net_conjoint)
            if conjoint_32600.attribution_enfants_act is not None:
                normaliser_enfant = lambda e: (normaliser(e[0]), e[1])
                ici = ((f.conjoint_enfant_nom, f.conjoint_enfant_naissance),
                       (f.enfant_nom, f.enfant_naissance))
                if tuple(map(normaliser_enfant, ici)) != tuple(map(normaliser_enfant, conjoint_32600.attribution_enfants_act)):
                    raise ValueError("Attribution des enfants ACT divergente entre les deux dossiers.")
                etudiants = (f.conjoint_etudiant, f.demandeur_etudiant or not p.pas_etudiant_temps_plein_plus_13_semaines)
                if etudiants != conjoint_32600.etudiants_act:
                    raise ValueError("Statuts étudiants ACT divergents entre les deux dossiers.")
            if f.conjoint_revenu_travail != conjoint_32600.revenu_travail_conjoint:
                raise ValueError("Revenu de travail du conjoint ACT divergent de son dossier 32600.")
            if conjoint_32600.ciph_conjoint_act_confirme and not f.conjoint_ciph:
                raise ValueError("Le CIPH du conjoint confirmé dans son ACT doit être repris dans ce profil.")
        if any(v != max(f.conjoint_revenu_net, ZERO) for v in revenus):
            raise ValueError("Revenu du conjoint ACT divergent de 30300/32600.")
    if personne_30400.reclamer_montant and f.conjoint_nom:
        raise ValueError("Le profil 30400 actuel est incompatible avec le conjoint déclaré pour l'ACT.")
    if supplement.reclamer:
        if not supplement.mode_familial:
            raise ValueError("ACT familial : utiliser le supplément médical familial 5T.")
        situation = "conjoint" if f.conjoint_nom else "sans conjoint"
        if supplement.situation_conjugale != situation or normaliser(supplement.nom_conjoint) != normaliser(f.conjoint_nom):
            raise ValueError("Situation conjugale divergente entre ACT et supplément médical.")
        if supplement.revenu_net_conjoint != f.conjoint_revenu_net:
            raise ValueError("Revenu du conjoint divergent entre ACT et supplément médical.")


def trace_act_familial_2025(r):
    return (
        ("Admissibilité étudiante ACT après attribution", ZERO,
         f"Demandeur admissible : {r.demandeur_admissible}; conjoint : {r.conjoint_admissible}; exception étudiante réservée au parent attributaire, 122.7(10)"),
        ("Revenu de travail familial ACT", r.travail_familial, "10100 demandeur + 10100 conjoint admissible; autres postes exclus du profil"),
        ("Revenu net familial avant exemption ACT", r.net_avant_exemption, "Somme des 23600 retenus, chacun borné à zéro; conjoint non admissible exclu"),
        ("Exemption du second revenu ACT", r.exemption_second_revenu, "min(16386, travail et net du même membre ayant le plus faible travail); à égalité, colonne conjoint"),
        ("Revenu familial ajusté ACT", r.net_familial, "Revenu net familial retenu moins exemption du second revenu"),
        ("ACT avant réduction", r.base_avant, f"Si demandée : min({r.plafond_base}, max(travail familial - {r.seuil_travail}, 0) x {r.taux_base})"),
        ("Réduction ACT", r.reduction_base, f"Si demandée : max(net familial - {r.seuil_reduction_base}, 0) x 20 %"),
        ("Supplément ACT avant réduction", r.supplement_avant, f"Si demandé : min(851.31, max(travail personnel - 1200, 0) x {r.taux_supplement})"),
        ("Réduction supplément ACT", r.reduction_supplement, f"Si demandé : max(net familial - {r.seuil_reduction_supplement}, 0) x {r.taux_reduction_supplement}"),
        ("ACT remboursable 45300", r.ligne_45300, "Base et supplément personnels après réductions, sans solde négatif"),
        ("Avances de base attribuées ACT", r.avances_base_retenues, "Cases 10 des deux conjoints attribuées au déclarant désigné; supplément case 11 conservé par son bénéficiaire"),
        ("Avances ACT 41500", r.ligne_41500, "min(45300, avances de base attribuées + propre case 11); ajouté à 42000, hors 42900"),
    )


def famille_act_depuis_dict(v):
    if v is None:
        return FamilleAllocation2025()
    if not isinstance(v, dict) or set(v) - {c.name for c in fields(FamilleAllocation2025)}:
        raise ValueError("Clés familiales ACT invalides.")
    valeurs = dict(v)
    for c in fields(FamilleAllocation2025):
        if c.type is Decimal:
            brut = valeurs.get(c.name, "0")
            if isinstance(brut, bool) or not isinstance(brut, (str, int)):
                raise ValueError("Montant familial ACT JSON invalide : " + c.name)
            try:
                valeurs[c.name] = Decimal(brut)
            except InvalidOperation as exc:
                raise ValueError("Montant familial ACT JSON invalide : " + c.name) from exc
    return valider_famille_act_2025(FamilleAllocation2025(**valeurs))
