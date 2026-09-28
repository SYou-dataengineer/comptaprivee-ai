"""Annexe 2 Québec 2025 : calcul à partir du dossier brut du conjoint.

Source : ARC 5005-S2 (25), lignes 1–13; 5005-R (25), ligne 100.
Les montants du conjoint sont recalculés, jamais saisis comme crédits dérivés.
"""
from dataclasses import dataclass, fields
from decimal import Decimal
import json

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")
CODES_LIGNE_100 = frozenset({
    "30800", "31000", "31200", "31217", "31205", "31210", "31215",
    "31220", "31240", "31260", "31270", "31285", "31300",
})
CONFIRMATIONS_TRANSFERT_CONJOINT = {
    "valide_par_comptable": "Les deux dossiers et l'annexe 2 sont validés par le comptable",
    "relation_confirmee": "Le dossier importé appartient à mon époux ou conjoint de fait",
    "residence_annee_confirmee": "Les deux conjoints sont résidents du Canada toute l'année et du Québec au 31 décembre 2025",
    "absence_rupture_90_jours": "Aucune séparation pour rupture d'au moins 90 jours comprenant le 31 décembre 2025",
    "dossier_avant_transfert": "Le dossier importé est le calcul personnel du conjoint avant le présent transfert, sans montant reçu à 32600",
    "autorisation_et_unicite": "Le conjoint autorise ce transfert; aucun montant transféré à un autre bénéficiaire ni réclamé deux fois",
    "aucun_traitement_special": "Aucun décès, faillite, résidence partielle ou traitement spécialisé omis dans les deux dossiers",
}


@dataclass(frozen=True)
class TransfertConjointFederal2025:
    activer: bool = False
    beneficiaire: str = ""
    dossier_conjoint_json: str = ""
    source: str = ""
    valide_par_comptable: bool = False
    relation_confirmee: bool = False
    residence_annee_confirmee: bool = False
    absence_rupture_90_jours: bool = False
    dossier_avant_transfert: bool = False
    autorisation_et_unicite: bool = False
    aucun_traitement_special: bool = False


@dataclass(frozen=True)
class ResultatTransfertConjoint2025:
    nom_conjoint: str = ""
    revenu_net_conjoint: Decimal = ZERO
    revenu_beneficiaire_declare_30300: Decimal | None = None
    age_30100: Decimal = ZERO
    enfant_30500: Decimal = ZERO
    pension_31400: Decimal = ZERO
    handicap_31600: Decimal = ZERO
    scolarite_36000: Decimal = ZERO
    total_ligne_6: Decimal = ZERO
    equivalent_ligne_7: Decimal = ZERO
    personnel_30000: Decimal = ZERO
    base_ligne_100: Decimal = ZERO
    scolarite_32300: Decimal = ZERO
    total_ligne_11: Decimal = ZERO
    reduction_36100: Decimal = ZERO
    ligne_32600: Decimal = ZERO
    revenu_beneficiaire_declare_45200: Decimal | None = None
    revenu_beneficiaire_declare_act: Decimal | None = None
    travail_beneficiaire_declare_act: Decimal | None = None
    act_base_beneficiaire_declare: bool | None = None
    act_base_conjoint_reclamee: bool = False
    revenu_travail_conjoint: Decimal = ZERO
    ciph_conjoint_act_confirme: bool = False
    attribution_enfants_act: tuple[tuple[str, str], tuple[str, str]] | None = None
    etudiants_act: tuple[bool, bool] | None = None
    enfants_30500: tuple[tuple[str, str, str], ...] = ()


def _montant(valeur, nom):
    if not isinstance(valeur, Decimal) or not valeur.is_finite() or valeur < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        return arrondir_cent(valeur)
    except ArithmeticError as erreur:
        raise ValueError(f"Montant hors capacité : {nom}.") from erreur


def calculer_annexe2_2025(*, revenu_imposable, impot_brut, montants_par_ligne, scolarite_designee=ZERO):
    """Fonction pure sur les lignes calculées du conjoint; aucun test d'admissibilité."""
    revenu = _montant(revenu_imposable, "26000 conjoint")
    brut = _montant(impot_brut, "Impôt brut conjoint")
    designation = _montant(scolarite_designee, "Désignation de scolarité")
    if designation > Decimal(5000):
        raise ValueError("La désignation de scolarité ne peut dépasser 5000 $.")
    montants = {}
    for code, valeur in montants_par_ligne:
        if code in montants:
            raise ValueError("Ligne du conjoint comptée deux fois : " + code)
        montants[code] = _montant(valeur, code)
    age, enfant, pension, handicap = (montants.get(c, ZERO) for c in ("30100", "30500", "31400", "31600"))
    if pension > Decimal(2000):
        raise ValueError("La ligne 31400 du conjoint ne peut dépasser 2000 $.")
    total = age + enfant + pension + handicap + designation
    equivalent = revenu if revenu <= Decimal(57375) else arrondir_cent(brut / Decimal("0.145"))
    personnel = montants.get("30000", ZERO)
    ligne100 = sum((montants.get(c, ZERO) for c in CODES_LIGNE_100), ZERO)
    scolarite = montants.get("32300", ZERO)
    deduction = personnel + ligne100 + scolarite
    reduction = max(equivalent - deduction, ZERO)
    return ResultatTransfertConjoint2025(
        age_30100=age, enfant_30500=enfant, pension_31400=pension, handicap_31600=handicap,
        scolarite_36000=designation, total_ligne_6=total, equivalent_ligne_7=equivalent,
        personnel_30000=personnel, base_ligne_100=ligne100, scolarite_32300=scolarite,
        total_ligne_11=deduction, reduction_36100=reduction, ligne_32600=max(total - reduction, ZERO),
    )


def valider_transfert_conjoint_2025(p):
    if not isinstance(p, TransfertConjointFederal2025):
        raise ValueError("Profil de transfert du conjoint invalide.")
    for nom in ("activer", *CONFIRMATIONS_TRANSFERT_CONJOINT):
        if type(getattr(p, nom)) is not bool:
            raise ValueError("Confirmation non booléenne : " + nom)
    for nom in ("beneficiaire", "dossier_conjoint_json", "source"):
        if not isinstance(getattr(p, nom), str):
            raise ValueError("Champ de transfert invalide : " + nom)
    if not p.activer:
        if p.dossier_conjoint_json.strip() or p.source.strip() or p.beneficiaire.strip():
            raise ValueError("Activez le transfert pour utiliser le dossier du conjoint.")
        return p
    if not p.source.strip() or not p.dossier_conjoint_json.strip() or not p.beneficiaire.strip():
        raise ValueError("Dossier brut du conjoint et source obligatoires.")
    for nom, libelle in CONFIRMATIONS_TRANSFERT_CONJOINT.items():
        if not getattr(p, nom):
            raise ValueError("Confirmation obligatoire : " + libelle)
    _contenu_conjoint(p.dossier_conjoint_json)
    return p


def _contenu_conjoint(texte):
    try:
        contenu = json.loads(texte)
    except (ValueError, TypeError, RecursionError) as erreur:
        raise ValueError("Le dossier JSON du conjoint est illisible.") from erreur
    if not isinstance(contenu, dict):
        raise ValueError("Le dossier du conjoint doit être un objet JSON.")
    transfert = contenu.get("transfert_conjoint", {})
    if not isinstance(transfert, dict) or any(transfert.values()):
        raise ValueError("Un dossier de conjoint contenant un transfert 32600 imbriqué n'est pas pris en charge.")
    if contenu.get("derniere_estimation") is not None or contenu.get("rapport_pdf") is not None:
        raise ValueError("L'instantané du conjoint doit contenir ses entrées, sans estimation ni rapport dérivé.")
    return contenu


def instantane_conjoint_2025(contenu):
    """Retire les résultats dérivés d'une sauvegarde; conserve les entrées et sources."""
    if not isinstance(contenu, dict):
        raise ValueError("Le dossier du conjoint doit être un objet JSON.")
    brut = dict(contenu)
    brut.pop("derniere_estimation", None)
    brut.pop("rapport_pdf", None)
    texte = json.dumps(brut, ensure_ascii=False, allow_nan=False)
    _contenu_conjoint(texte)
    return texte


def recalculer_dossier_conjoint_2025(p):
    """Rejoue les mêmes profils que le dossier principal, sans lire de documents."""
    from .tax_case_storage import dossier_fiscal_depuis_contenu
    from .tax_estimation_2025 import calculer_estimation_fiscale_2025
    valider_transfert_conjoint_2025(p)
    if not p.activer:
        return None
    c = dossier_fiscal_depuis_contenu(_contenu_conjoint(p.dossier_conjoint_json), verifier_documents=False)
    meta = {"chemin", "dossier", "sauvegarde_le", "estimation", "rapport_pdf", "documents_manquants"}
    entrees = {f.name: getattr(c, f.name) for f in fields(c) if f.name not in meta}
    return calculer_estimation_fiscale_2025(c.dossier, **entrees)


def calculer_transfert_conjoint_2025(p, *, beneficiaire):
    from dataclasses import replace
    valider_transfert_conjoint_2025(p)
    if not p.activer:
        return ResultatTransfertConjoint2025()
    conjoint = recalculer_dossier_conjoint_2025(p)
    normaliser = lambda s: " ".join(s.split()).casefold()
    if normaliser(p.beneficiaire) != normaliser(beneficiaire):
        raise ValueError("Le bénéficiaire du transfert a changé; confirmez de nouveau l'autorisation.")
    if normaliser(conjoint.dossier.client) == normaliser(beneficiaire):
        raise ValueError("Le conjoint et le bénéficiaire doivent être deux personnes distinctes.")
    act, supp = conjoint.allocation_travailleurs, conjoint.frais_medicaux.supplement
    if (act.present and not act.famille.activer) or (supp.reclamer and not supp.mode_familial):
        raise ValueError("Le dossier du conjoint contient un crédit réservé au profil individuel sans conjoint.")
    if supp.reclamer and (supp.situation_conjugale != "conjoint" or normaliser(supp.nom_conjoint) != normaliser(beneficiaire)):
        raise ValueError("Le conjoint déclaré pour 45200 doit être le bénéficiaire de 32600.")
    if act.famille.activer and (normaliser(act.famille.conjoint_nom) != normaliser(beneficiaire) or not act.famille.conjoint_resident):
        raise ValueError("Le conjoint ACT déclaré doit être le bénéficiaire 32600, résident canadien toute l'année.")
    transfert = conjoint.frais_scolarite.reports_federaux.transfert_sortant
    if transfert.present and (transfert.relation != "conjoint" or normaliser(transfert.beneficiaire) != normaliser(beneficiaire)):
        raise ValueError("La désignation de scolarité doit viser exclusivement ce conjoint bénéficiaire.")
    r = calculer_annexe2_2025(
        revenu_imposable=conjoint.revenu.revenu_imposable_federal,
        impot_brut=conjoint.federal.impot_brut,
        montants_par_ligne=conjoint.federal.credits_federaux_complets.montants_par_ligne,
        scolarite_designee=transfert.montant_designe,
    )
    return replace(r, nom_conjoint=conjoint.dossier.client, revenu_net_conjoint=conjoint.revenu.revenu_net_federal,
        enfants_30500=tuple((e.reference, e.nom, e.naissance) for e in conjoint.aidant_enfant_federal.enfants_detailles),
        revenu_beneficiaire_declare_45200=(max(supp.revenu_net_conjoint, ZERO) if supp.reclamer else None),
        revenu_beneficiaire_declare_act=(max(act.famille.conjoint_revenu_net, ZERO) if act.famille.activer else None),
        travail_beneficiaire_declare_act=(act.famille.conjoint_revenu_travail if act.famille.activer else None),
        act_base_beneficiaire_declare=(act.famille.conjoint_reclame_base if act.famille.activer else None),
        act_base_conjoint_reclamee=act.reclamer_base,
        attribution_enfants_act=(((act.famille.enfant_nom, act.famille.enfant_naissance),
            (act.famille.conjoint_enfant_nom, act.famille.conjoint_enfant_naissance)) if act.famille.activer else None),
        etudiants_act=((act.famille.demandeur_etudiant or not act.pas_etudiant_temps_plein_plus_13_semaines,
            act.famille.conjoint_etudiant) if act.famille.activer else None),
        revenu_travail_conjoint=conjoint.base.revenu_emploi_federal,
        ciph_conjoint_act_confirme=act.present and act.admissibilite_ciph_confirmee,
        revenu_beneficiaire_declare_30300=(conjoint.montant_conjoint_federal.revenu_net_conjoint_2025
            if conjoint.montant_conjoint_federal.reclamer_montant else None))


def lignes_transfert_conjoint_2025(p, r):
    if not p.activer:
        return []
    return ["", "TRANSFERT FÉDÉRAL DU CONJOINT — ANNEXE 2 / BLOC 5K",
        f"Conjoint : {r.nom_conjoint}; source : {p.source}; validation comptable confirmée",
        "Dossier personnel du conjoint recalculé avant transfert; aucune lecture des pièces sources.",
        f"30100 : {r.age_30100:.2f}; 30500 : {r.enfant_30500:.2f}; 31400 : {r.pension_31400:.2f}; 31600 : {r.handicap_31600:.2f} $",
        *(f"Enfant à 30500 du conjoint : {ref} — {nom}, naissance {naissance}; attribution au conjoint avant transfert."
          for ref, nom, naissance in r.enfants_30500),
        f"Scolarité désignée 36000 : {r.scolarite_36000:.2f}; total annexe 2 ligne 6 : {r.total_ligne_6:.2f} $",
        f"Équivalent imposable ligne 7 (26000 ou impôt brut / 14,5 %) : {r.equivalent_ligne_7:.2f} $",
        f"30000 : {r.personnel_30000:.2f}; T1 Québec ligne 100 : {r.base_ligne_100:.2f}; 32300 : {r.scolarite_32300:.2f} $",
        f"Réduction 36100 = max(ligne 7 - {r.total_ligne_11:.2f}, 0) : {r.reduction_36100:.2f} $",
        f"Ligne 32600 = max(ligne 6 - 36100, 0) : {r.ligne_32600:.2f} $",
        "Base ajoutée une fois à 33500; 33800, 34990, 35000 recalculés; aucun transfert Québec."]
