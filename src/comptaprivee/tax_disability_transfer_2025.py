"""Calcul préparatoire 31800 : LIR 118.3(2), folio S1-F1-C2, paragraphe 2.37.

Entrées de calcul internes issues d'une estimation du donneur, pas une saisie
de montants dérivés. L'admissibilité et l'intégration applicative sont distinctes.
"""
from dataclasses import asdict, dataclass, fields
from datetime import date
from decimal import Decimal
import json

from .tax_rules_2025 import arrondir_cent
from .tax_federal_top_up_2025 import calculer_credit_compensatoire_2025

ZERO = Decimal("0")
TAUX = Decimal("0.145")
# Crédits des articles 118 à 118.07 et 118.7 : T1 Québec ligne 102.
CODES_AVANT_HANDICAP = frozenset({
    "30000", "30100", "30300", "30400", "30425", "30450", "30500",
    "30800", "31000", "31200", "31217", "31205", "31210", "31215",
    "31220", "31240", "31260", "31270", "31285", "31300", "31400",
})


@dataclass(frozen=True)
class CalculTransfertHandicap2025:
    montant_31600: Decimal
    base_ligne_102: Decimal
    credits_avant_handicap: Decimal
    compensatoire_avant_handicap: Decimal
    impot_avant_handicap: Decimal
    credit_handicap: Decimal
    credit_disponible: Decimal
    base_disponible: Decimal

    @property
    def credit_utilise(self) -> Decimal:
        """DTC absorbé par l'impôt hypothétique défini à 118.3(2)d)."""
        return self.credit_handicap - self.credit_disponible

    @property
    def base_utilisee(self) -> Decimal:
        """Complément de la base transférable, arrondi au cent."""
        return self.montant_31600 - self.base_disponible


def _montant(v, nom):
    if not isinstance(v, Decimal) or not v.is_finite() or v < ZERO:
        raise ValueError(f"{nom} doit être un Decimal fini non négatif.")
    try:
        if v != arrondir_cent(v):
            raise ValueError(f"{nom} exige au plus deux décimales.")
    except ArithmeticError as erreur:
        raise ValueError(f"{nom} hors capacité.") from erreur
    return v


def calculer_disponible_handicap_2025(*, montant_31600, impot_brut, montants_par_ligne,
                                      ajouts_impot_partie_i=ZERO):
    """Impôt hypothétique du donneur avant crédits non permis par 118.3(2)d).

Les remboursements, dividendes, dons, frais médicaux, scolarité, crédits
politiques et fonds ne réduisent pas cet impôt hypothétique. Le crédit
compensatoire 118(11) est recalculé sur les seuls crédits permis.
"""
    handicap = _montant(montant_31600, "31600 du donneur")
    brut = _montant(impot_brut, "Impôt brut du donneur")
    ajouts = _montant(ajouts_impot_partie_i, "Ajouts à l'impôt de la partie I")
    if handicap > Decimal(16052):
        raise ValueError("31600 dépasse le maximum fédéral 2025, supplément compris.")
    if type(montants_par_ligne) is not tuple:
        raise ValueError("Les lignes recalculées du donneur doivent former un tuple.")
    lignes = {}
    for element in montants_par_ligne:
        if type(element) is not tuple or len(element) != 2:
            raise ValueError("Ligne du donneur invalide.")
        code, valeur = element
        if not isinstance(code, str) or code in lignes:
            raise ValueError("Ligne du donneur invalide ou dupliquée.")
        lignes[code] = _montant(valeur, code)
    base = _montant(sum((v for c, v in lignes.items() if c in CODES_AVANT_HANDICAP), ZERO), "Base ligne 102")
    credits = arrondir_cent(base * TAUX)
    compensatoire = calculer_credit_compensatoire_2025(credits, ZERO)
    impot = max(brut - credits - compensatoire, ZERO) + ajouts
    credit = arrondir_cent(handicap * TAUX)
    disponible = max(credit - impot, ZERO)
    return CalculTransfertHandicap2025(handicap, base, credits, compensatoire, impot,
        credit, disponible, min(handicap, arrondir_cent(disponible / TAUX)))


LIENS_HANDICAP = ("enfant", "petit-enfant", "parent", "grand-parent", "frère ou sœur",
                  "oncle ou tante", "neveu ou nièce")
CONDITIONS_HANDICAP = ("30400 réclamé", "30400 admissible sans conjoint ni revenu du donneur",
    "30450 réclamé", "30450 admissible sans revenu ni condition d'âge du donneur")
SITUATIONS_PENSION_HANDICAP = ("aucun paiement exigible", "séparation partielle sans déduction 22000",
                              "obligations réciproques avec accord")
CONFIRMATIONS_HANDICAP_TRANSFERE = {
    "valide_par_comptable": "Deux dossiers, pièces et calcul du transfert vérifiés par le comptable",
    "soutien_regulier": "Le donneur dépend réellement du contribuable pour nourriture, logement ou vêtements, régulièrement et de façon constante",
    "conditions_verifiees": "Lien familial et conditions 30400/30450 indiquées vérifiés, y compris les conditions hypothétiques si utilisées",
    "concurrence_verifiee": "Demandes du conjoint du donneur et des autres personnes de soutien vérifiées; aucune omission",
    "pension_verifiee": "Obligations alimentaires vérifiées; toute exception invoquée et l'accord sont justifiés sur pièces",
    "autorisation_partage": "Le donneur autorise le transfert; l'accord de partage et toutes les parts des autres soutiens sont vérifiés",
    "avant_transfert": "L'instantané est le dossier personnel du donneur avant le présent transfert, avec son CIPH approuvé pour 2025",
    "profil_ordinaire": "Donneur résident du Québec et du Canada toute l'année 2025; aucun décès, faillite ou traitement spécial omis",
}


@dataclass(frozen=True)
class PartHandicapAutreSoutien2025:
    personne: str = ""
    montant_base: Decimal = ZERO
    source: str = ""


@dataclass(frozen=True)
class TransfertHandicapDependant2025:
    reference: str = ""
    nom_donneur: str = ""
    naissance: str = ""
    lien: str = ""
    lien_avec_conjoint: bool = False
    condition: str = ""
    dossier_donneur_json: str = ""
    source: str = ""
    rapprochement_30400_30450: str = ""
    conjoint_donneur_reclame: bool = False
    autre_personne_reclame_30400: bool = False
    situation_pension: str = "aucun paiement exigible"
    source_pension: str = ""
    autres_parts: tuple[PartHandicapAutreSoutien2025, ...] = ()
    limiter_demande: bool = False
    part_demandee: Decimal = ZERO
    valide_par_comptable: bool = False
    soutien_regulier: bool = False
    conditions_verifiees: bool = False
    concurrence_verifiee: bool = False
    pension_verifiee: bool = False
    autorisation_partage: bool = False
    avant_transfert: bool = False
    profil_ordinaire: bool = False


@dataclass(frozen=True)
class TransfertsHandicap2025:
    beneficiaire: str = ""
    transferts: tuple[TransfertHandicapDependant2025, ...] = ()


@dataclass(frozen=True)
class ResultatHandicapDependant2025:
    nom: str
    revenu_net: Decimal
    revenu_imposable: Decimal
    calcul: CalculTransfertHandicap2025
    autres_parts: Decimal
    base_retenue: Decimal


@dataclass(frozen=True)
class ResultatTransfertsHandicap2025:
    donneurs: tuple[ResultatHandicapDependant2025, ...] = ()
    ligne_31800: Decimal = ZERO


def _cle(v):
    return " ".join(v.split()).casefold()


def _contenu_donneur(texte):
    try:
        c = json.loads(texte)
    except (ValueError, TypeError, RecursionError) as erreur:
        raise ValueError("Dossier brut du donneur illisible.") from erreur
    if not isinstance(c, dict):
        raise ValueError("Dossier brut du donneur invalide.")
    for nom in ("transferts_handicap", "transfert_conjoint"):
        profil = c.get(nom, {})
        if not isinstance(profil, dict) or any(profil.values()):
            raise ValueError("Importer le dossier personnel avant transferts : les instantanés 31800/32600 imbriqués ne sont pas pris en charge.")
    if c.get("derniere_estimation") is not None or c.get("rapport_pdf") is not None:
        raise ValueError("Le dossier du donneur doit contenir les entrées brutes, sans résultats dérivés.")
    return c


def instantane_donneur_handicap_2025(contenu):
    if not isinstance(contenu, dict):
        raise ValueError("Dossier du donneur invalide.")
    c = dict(contenu)
    c.pop("derniere_estimation", None)
    c.pop("rapport_pdf", None)
    try:
        texte = json.dumps(c, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, RecursionError) as erreur:
        raise ValueError("Dossier du donneur non sérialisable.") from erreur
    _contenu_donneur(texte)
    return texte


def valider_transferts_handicap_2025(p):
    if not isinstance(p, TransfertsHandicap2025) or type(p.transferts) is not tuple or not isinstance(p.beneficiaire, str):
        raise ValueError("Profil des transferts handicap invalide.")
    if bool(p.transferts) != bool(p.beneficiaire.strip()):
        raise ValueError("Le bénéficiaire est obligatoire seulement pour un profil actif.")
    references, noms, compte_30400 = set(), set(), 0
    for t in p.transferts:
        if not isinstance(t, TransfertHandicapDependant2025):
            raise ValueError("Transfert handicap invalide.")
        for f in fields(t):
            v = getattr(t, f.name)
            if f.type is bool and type(v) is not bool:
                raise ValueError("Confirmation non booléenne : " + f.name)
            if f.type is str and not isinstance(v, str):
                raise ValueError("Texte invalide : " + f.name)
        for nom in ("reference", "nom_donneur", "naissance", "source", "rapprochement_30400_30450", "dossier_donneur_json"):
            if not getattr(t, nom).strip():
                raise ValueError("Champ obligatoire : " + nom)
        try:
            naissance = date.fromisoformat(t.naissance)
            if naissance.isoformat() != t.naissance or naissance.year > 2025:
                raise ValueError()
        except ValueError as erreur:
            raise ValueError("Naissance du donneur invalide, format AAAA-MM-JJ requis.") from erreur
        if t.lien not in LIENS_HANDICAP or t.condition not in CONDITIONS_HANDICAP:
            raise ValueError("Lien ou condition d'admissibilité invalide; conjoint : 32600 distinct.")
        if t.conjoint_donneur_reclame or t.autre_personne_reclame_30400:
            raise ValueError("Transfert exclu : conjoint du donneur réclamant un crédit personnel/transfert, ou autre réclamant 30400.")
        if _cle(t.reference) in references or _cle(t.nom_donneur) in noms or _cle(t.nom_donneur) == _cle(p.beneficiaire):
            raise ValueError("Donneur dupliqué ou identique au bénéficiaire.")
        references.add(_cle(t.reference))
        noms.add(_cle(t.nom_donneur))
        for nom, libelle in CONFIRMATIONS_HANDICAP_TRANSFERE.items():
            if not getattr(t, nom):
                raise ValueError("Confirmation obligatoire : " + libelle)
        if t.situation_pension not in SITUATIONS_PENSION_HANDICAP:
            raise ValueError("Situation de pension alimentaire invalide.")
        if t.situation_pension != "aucun paiement exigible" and (t.lien != "enfant" or not t.source_pension.strip()):
            raise ValueError("L'exception alimentaire exige un enfant et ses pièces justificatives.")
        if type(t.autres_parts) is not tuple:
            raise ValueError("Les parts des autres soutiens doivent former un tuple.")
        soutiens = set()
        for a in t.autres_parts:
            if not isinstance(a, PartHandicapAutreSoutien2025):
                raise ValueError("Part de soutien invalide.")
            if not isinstance(a.personne, str) or not a.personne.strip() or not isinstance(a.source, str) or not a.source.strip():
                raise ValueError("Nom et source de l'autre soutien obligatoires.")
            if _cle(a.personne) in soutiens or _cle(a.personne) in (_cle(p.beneficiaire), _cle(t.nom_donneur)):
                raise ValueError("Autre soutien dupliqué ou incompatible.")
            soutiens.add(_cle(a.personne))
            _montant(a.montant_base, "Part de l'autre soutien")
        if t.condition == "30400 réclamé":
            compte_30400 += 1
            if any(a.montant_base for a in t.autres_parts):
                raise ValueError("La personne réclamant 30400 est la seule autorisée à recevoir ce transfert.")
        _montant(t.part_demandee, "Choix de part de base")
        if not t.limiter_demande and t.part_demandee:
            raise ValueError("Activez le choix d'une part limitée pour saisir cette part.")
        _contenu_donneur(t.dossier_donneur_json)
    if compte_30400 > 1:
        raise ValueError("Un seul donneur peut correspondre à la demande 30400 du contribuable.")
    return p


def calculer_transferts_handicap_2025(p, *, beneficiaire, annee=2025,
                                     reclame_30400=None, reclame_30450=None, deduction_22000=ZERO):
    from .tax_case_storage import dossier_fiscal_depuis_contenu
    from .tax_estimation_2025 import calculer_estimation_fiscale_2025
    valider_transferts_handicap_2025(p)
    _montant(deduction_22000, "Déduction 22000")
    if not p.transferts:
        return ResultatTransfertsHandicap2025()
    if annee != 2025 or not isinstance(beneficiaire, str) or _cle(p.beneficiaire) != _cle(beneficiaire):
        raise ValueError("Année ou bénéficiaire du transfert modifié : autorisation à refaire.")
    resultats = []
    for t in p.transferts:
        if (t.condition == "30400 réclamé" and reclame_30400 is False) or (t.condition == "30450 réclamé" and reclame_30450 is False):
            raise ValueError("La ligne indiquée comme réclamée est absente du dossier bénéficiaire.")
        if t.situation_pension == "séparation partielle sans déduction 22000" and deduction_22000:
            raise ValueError("Cette exception alimentaire est incompatible avec une déduction 22000.")
        c = dossier_fiscal_depuis_contenu(_contenu_donneur(t.dossier_donneur_json), verifier_documents=False)
        if c.dossier.annee_fiscale != 2025:
            raise ValueError("Le dossier du donneur doit porter sur 2025.")
        meta = {"chemin", "dossier", "sauvegarde_le", "estimation", "rapport_pdf", "documents_manquants"}
        entrees = {f.name: getattr(c, f.name) for f in fields(c) if f.name not in meta}
        donneur = calculer_estimation_fiscale_2025(c.dossier, **entrees)
        if _cle(donneur.dossier.client) != _cle(t.nom_donneur):
            raise ValueError("Le nom du donneur ne correspond pas à son dossier.")
        handicap = donneur.credit_deficience
        if not handicap.reclamer_federal:
            raise ValueError("Le dossier du donneur doit contenir son CIPH fédéral approuvé et validé.")
        if handicap.naissance_federale:
            if handicap.naissance_federale != t.naissance:
                raise ValueError("Naissance divergente entre le transfert et le dossier du donneur.")
        elif date.fromisoformat(t.naissance) > date(2007, 1, 1):
            raise ValueError("Donneur mineur ou devenu majeur : renseigner son handicap détaillé dans son dossier.")
        lignes = donneur.federal.credits_federaux_complets.montants_par_ligne
        r = calculer_disponible_handicap_2025(montant_31600=dict(lignes).get("31600", ZERO),
            impot_brut=donneur.federal.impot_brut, montants_par_ligne=lignes,
            ajouts_impot_partie_i=donneur.rapprochement.avances_act_ligne_41500)
        autres = sum((a.montant_base for a in t.autres_parts), ZERO)
        disponible = r.base_disponible - autres
        if disponible < ZERO or (t.limiter_demande and t.part_demandee > disponible):
            raise ValueError("Les parts désignées dépassent le handicap réellement disponible du donneur.")
        retenue = t.part_demandee if t.limiter_demande else disponible
        resultats.append(ResultatHandicapDependant2025(t.nom_donneur, donneur.revenu.revenu_net_federal,
            donneur.revenu.revenu_imposable_federal, r, autres, retenue))
    return ResultatTransfertsHandicap2025(tuple(resultats), sum((r.base_retenue for r in resultats), ZERO))


def transferts_handicap_vers_dict(p):
    valider_transferts_handicap_2025(p)
    def convertir(v):
        if isinstance(v, Decimal):
            return format(v, ".2f")
        if isinstance(v, dict):
            return {k: convertir(x) for k, x in v.items()}
        if isinstance(v, (tuple, list)):
            return [convertir(x) for x in v]
        return v
    return convertir(asdict(p))


def lignes_transferts_handicap_2025(p, r):
    if not p.transferts:
        return ()
    lignes = ["TRANSFERTS HANDICAP — LIGNE 31800 — VALIDÉS PAR LE COMPTABLE",
        "Admissibilité documentée par le comptable; dossiers bruts des donneurs recalculés.",
        "LIR 118.3(2) : crédit disponible après impôt hypothétique, puis conversion en base à 14,5 %."]
    for t, d in zip(p.transferts, r.donneurs):
        c = d.calcul
        lignes.extend((
            f"Donneur : {t.nom_donneur}; référence : {t.reference}; naissance : {t.naissance}.",
            f"Lien : {t.lien}" + (" du conjoint" if t.lien_avec_conjoint else " du contribuable") + f"; condition : {t.condition}.",
            f"Source : {t.source}; rapprochement 30400/30450 : {t.rapprochement_30400_30450}.",
            f"Pension alimentaire : {t.situation_pension}; pièces : {t.source_pension or 'sans objet'}.",
            f"Donneur : net {d.revenu_net:.2f} $; imposable {d.revenu_imposable:.2f} $; base 31600 {c.montant_31600:.2f} $.",
            f"Base 102 {c.base_ligne_102:.2f} $; crédits permis {c.credits_avant_handicap:.2f} $; compensatoire permis {c.compensatoire_avant_handicap:.2f} $.",
            f"Impôt hypothétique {c.impot_avant_handicap:.2f} $; crédit handicap {c.credit_handicap:.2f} $; crédit disponible {c.credit_disponible:.2f} $.",
            f"Crédit DTC : disponible {c.credit_handicap:.2f} $ - utilisé {c.credit_utilise:.2f} $ = inutilisé {c.credit_disponible:.2f} $.",
            f"Base DTC : disponible {c.montant_31600:.2f} $ - utilisée {c.base_utilisee:.2f} $ = inutilisée {c.base_disponible:.2f} $ (arrondi au cent).",
            f"Base disponible {c.base_disponible:.2f} $; autres parts {d.autres_parts:.2f} $; base retenue {d.base_retenue:.2f} $.",
        ))
        lignes.extend(f"Autre soutien : {a.personne}; part de base {a.montant_base:.2f} $; source : {a.source}." for a in t.autres_parts)
        if t.limiter_demande:
            lignes.append(f"Part limitée désignée : {t.part_demandee:.2f} $.")
    lignes.extend((f"Ligne 31800 : {r.ligne_31800:.2f} $; incluse une fois avant scolarité dans 33500.",
        "Revenus et calcul Québec inchangés; profils ordinaires 2025 seulement; instantanés de transferts imbriqués non pris en charge."))
    return tuple(lignes)


def transferts_handicap_depuis_dict(valeur):
    enfants = {TransfertsHandicap2025: ("transferts", TransfertHandicapDependant2025),
               TransfertHandicapDependant2025: ("autres_parts", PartHandicapAutreSoutien2025)}
    def lire(v, classe):
        if not isinstance(v, dict) or set(v) - {f.name for f in fields(classe)}:
            raise ValueError("Champs du transfert handicap invalides.")
        v = dict(v)
        if classe in enfants:
            nom, enfant = enfants[classe]
            lignes = v.get(nom, [])
            if not isinstance(lignes, list):
                raise ValueError("Liste du transfert handicap invalide.")
            v[nom] = tuple(lire(x, enfant) for x in lignes)
        for f in fields(classe):
            if f.type is Decimal:
                x = v.get(f.name, "0")
                if not isinstance(x, (str, int)) or isinstance(x, bool):
                    raise ValueError("Montant du transfert handicap invalide.")
                try:
                    v[f.name] = _montant(Decimal(x), f.name)
                except (ArithmeticError, ValueError) as erreur:
                    raise ValueError("Montant du transfert handicap invalide.") from erreur
        return classe(**v)
    return valider_transferts_handicap_2025(lire({} if valeur is None else valeur, TransfertsHandicap2025))
