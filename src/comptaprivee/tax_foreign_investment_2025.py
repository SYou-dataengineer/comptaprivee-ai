"""Bloc 3G — socle prudent pour revenus de placement étrangers 2025.

Ce premier socle couvre uniquement une paire T5/RL-3 validée, déjà exprimée
en dollars canadiens, pour un revenu étranger non commercial d'un seul pays
et d'un seul titulaire.

Il NE calcule PAS encore le crédit T2209/40500 ni TP-772/409. Cette étape
est volontairement séparée afin de tester d'abord l'appariement et les
garde-fous sans toucher à l'orchestrateur fiscal.

Sources officielles 2025:
- ARC T5 cases 15/16
- ARC ligne 12100
- ARC T2209 / ligne 40500
- Revenu Québec RL-3 F/G
- Revenu Québec TP-772 / ligne 409
Voir docs/moteur_fiscal_2025.md.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_field_validation import STATUT_VALIDE, STATUT_CORRIGE_VALIDE
from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025

ZERO = Decimal("0")
MAX_MONTANT = Decimal("999999999.99")


@dataclass(frozen=True)
class ProfilPlacementEtranger2025:
    source: str = ""
    confirme: bool = False
    pays: str = ""
    devise: str = "CAD"
    titulaire_unique: bool = True
    revenu_non_commercial: bool = True
    aucun_revenu_exonere_convention: bool = True
    aucun_compte_conjoint: bool = True
    aucune_entreprise: bool = True
    aucune_pension_etrangere: bool = True
    aucun_gain_capital_etranger: bool = True
    aucune_situation_multi_pays: bool = True
    obligations_biens_etrangers_verifiees: bool = False


@dataclass(frozen=True)
class PlacementEtranger2025:
    revenu_brut_federal: Decimal = ZERO
    revenu_brut_quebec: Decimal = ZERO
    impot_etranger_federal: Decimal = ZERO
    impot_etranger_quebec: Decimal = ZERO
    pays: str = ""
    cotisation_fss: Decimal = ZERO
    present: bool = False


def _valider_montant(montant: Decimal, libelle: str) -> None:
    if (
        not isinstance(montant, Decimal)
        or not montant.is_finite()
        or montant < ZERO
        or montant > MAX_MONTANT
        or montant != montant.quantize(Decimal(".01"))
    ):
        raise ValueError(
            f"{libelle} invalide : montant fini, non négatif et au cent près requis."
        )


def valider_profil_placement_etranger_2025(
    profil: ProfilPlacementEtranger2025,
) -> ProfilPlacementEtranger2025:
    if not isinstance(profil, ProfilPlacementEtranger2025):
        raise ValueError("Profil placement étranger invalide.")

    champs_bool = (
        "confirme",
        "titulaire_unique",
        "revenu_non_commercial",
        "aucun_revenu_exonere_convention",
        "aucun_compte_conjoint",
        "aucune_entreprise",
        "aucune_pension_etrangere",
        "aucun_gain_capital_etranger",
        "aucune_situation_multi_pays",
        "obligations_biens_etrangers_verifiees",
    )
    for nom in champs_bool:
        if type(getattr(profil, nom)) is not bool:
            raise ValueError("Les confirmations du profil étranger doivent être booléennes.")

    if not isinstance(profil.source, str) or not isinstance(profil.pays, str):
        raise ValueError("Source et pays doivent être du texte.")
    if not isinstance(profil.devise, str):
        raise ValueError("Devise invalide.")

    if profil.devise != "CAD":
        raise ValueError(
            "Bloc 3G initial : les montants des feuillets doivent déjà être en CAD. "
            "Aucune conversion implicite."
        )

    exclusions = (
        not profil.titulaire_unique
        or not profil.revenu_non_commercial
        or not profil.aucun_revenu_exonere_convention
        or not profil.aucun_compte_conjoint
        or not profil.aucune_entreprise
        or not profil.aucune_pension_etrangere
        or not profil.aucun_gain_capital_etranger
        or not profil.aucune_situation_multi_pays
    )
    if exclusions:
        raise ValueError(
            "Placement étranger hors périmètre 3G initial : conjoint, entreprise, "
            "pension, gain en capital, convention ambiguë ou plusieurs pays."
        )

    if profil.confirme:
        if not profil.source.strip():
            raise ValueError("Justificatif du placement étranger obligatoire.")
        if not profil.pays.strip():
            raise ValueError("Pays étranger obligatoire.")
        if not profil.obligations_biens_etrangers_verifiees:
            raise ValueError(
                "Vérifiez explicitement les obligations T1135/TP-1079.8.BE avant confirmation."
            )

    return profil


def detecter_placement_etranger_2025(dossier) -> bool:
    cases = {"T5": {"15", "16"}, "RL-3": {"F", "G"}}
    return any(
        d.case in cases.get(d.type_document, set()) and d.valeur_validee != ZERO
        for d in dossier.donnees_validees
    )


def consolider_placement_etranger_2025(
    dossier,
    profil: ProfilPlacementEtranger2025,
) -> PlacementEtranger2025:
    valider_profil_placement_etranger_2025(profil)
    if not profil.confirme:
        raise ValueError("Confirmez le profil de placement étranger 2025.")

    if dossier.annee_fiscale != 2025 or dossier.province.casefold() not in {
        "québec",
        "quebec",
    }:
        raise ValueError("Placement étranger : dossier Québec 2025 requis.")

    autorises = {"T4", "RL-1", "T5", "RL-3"}
    if any(d.type_document not in autorises for d in dossier.donnees_validees):
        raise ValueError(
            "Placement étranger combiné avec d'autres placements ou prestations : "
            "hors périmètre 3G initial."
        )

    pieces = {p.resolve() for p in dossier.documents}
    donnees_pieces = {d.document.resolve() for d in dossier.donnees_validees}
    if pieces != donnees_pieces:
        raise ValueError(
            "Chaque pièce du dossier doit avoir des données validées; "
            "document non traité hors périmètre 3G."
        )

    valeurs = {}
    documents = {"T5": set(), "RL-3": set()}

    for d in dossier.donnees_validees:
        if d.type_document not in documents:
            continue

        cle = (d.type_document, d.case)
        if cle in valeurs:
            raise ValueError(
                "Case étrangère dupliquée; plusieurs feuillets ou plusieurs pays "
                "hors périmètre 3G initial."
            )
        if d.statut not in {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}:
            raise ValueError("Validation des cases étrangères manquante.")

        montant = d.valeur_validee
        _valider_montant(montant, f"{d.type_document} {d.case}")
        valeurs[cle] = montant
        documents[d.type_document].add(d.document.resolve())

    if any(len(v) != 1 for v in documents.values()):
        raise ValueError("Une seule paire T5/RL-3 est requise pour 3G initial.")
    if documents["T5"] & documents["RL-3"]:
        raise ValueError("T5 et RL-3 doivent être deux pièces distinctes.")

    requis = {
        ("T5", "15"),
        ("T5", "16"),
        ("RL-3", "F"),
        ("RL-3", "G"),
    }
    if not requis <= valeurs.keys():
        raise ValueError(
            "Les cases T5 15/16 et RL-3 F/G sont obligatoires, même lorsque l'impôt est nul."
        )

    if ("T5", "23") in valeurs and valeurs[("T5", "23")] != Decimal("1.00"):
        raise ValueError("T5 23 : seul un titulaire unique est couvert.")

    autorisees = requis | {("T5", "23")}
    if any(montant and cle not in autorisees for cle, montant in valeurs.items()):
        raise ValueError(
            "Autre case T5/RL-3 non nulle : intérêts/dividendes canadiens, rente, "
            "gain ou cas mixte hors périmètre 3G initial."
        )

    revenu_t5 = valeurs[("T5", "15")]
    impot_t5 = valeurs[("T5", "16")]
    revenu_rl3 = valeurs[("RL-3", "F")]
    impot_rl3 = valeurs[("RL-3", "G")]

    if revenu_t5 != revenu_rl3:
        raise ValueError(
            "T5 15 et RL-3 F doivent correspondre exactement dans le périmètre 3G initial."
        )
    if impot_t5 != impot_rl3:
        raise ValueError(
            "T5 16 et RL-3 G doivent correspondre exactement dans le périmètre 3G initial."
        )
    if impot_t5 > revenu_t5:
        raise ValueError(
            "Impôt étranger supérieur au revenu brut : dossier à revoir manuellement."
        )

    return PlacementEtranger2025(
        revenu_brut_federal=revenu_t5,
        revenu_brut_quebec=revenu_rl3,
        impot_etranger_federal=impot_t5,
        impot_etranger_quebec=impot_rl3,
        pays=profil.pays.strip(),
        cotisation_fss=cotisation_fss_prestations_2025(revenu_rl3),
        present=True,
    )


def appliquer_placement_etranger_2025(revenu, placement: PlacementEtranger2025):
    """Ajoute le revenu étranger brut une seule fois par juridiction.

    Le crédit pour impôt étranger n'est volontairement PAS appliqué ici.
    L'impôt étranger payé n'est pas une retenue canadienne et ne réduit pas
    le revenu brut.
    """
    if not isinstance(placement, PlacementEtranger2025):
        raise ValueError("Résultat de placement étranger invalide.")

    if not placement.present:
        return revenu

    _valider_montant(placement.revenu_brut_federal, "Revenu étranger fédéral")
    _valider_montant(placement.revenu_brut_quebec, "Revenu étranger Québec")
    _valider_montant(placement.impot_etranger_federal, "Impôt étranger fédéral")
    _valider_montant(placement.impot_etranger_quebec, "Impôt étranger Québec")

    if placement.revenu_brut_federal != placement.revenu_brut_quebec:
        raise ValueError(
            "Bloc 3G initial : le revenu étranger fédéral et Québec doit être apparié."
        )

    return replace(
        revenu,
        revenu_total_federal=revenu.revenu_total_federal
        + placement.revenu_brut_federal,
        revenu_net_federal=revenu.revenu_net_federal
        + placement.revenu_brut_federal,
        revenu_imposable_federal=revenu.revenu_imposable_federal
        + placement.revenu_brut_federal,
        revenu_total_quebec=revenu.revenu_total_quebec
        + placement.revenu_brut_quebec,
        revenu_net_quebec=revenu.revenu_net_quebec
        + placement.revenu_brut_quebec,
        revenu_imposable_quebec=revenu.revenu_imposable_quebec
        + placement.revenu_brut_quebec,
        profil="Placement étranger non commercial Québec 2025",
        limitations=(
            "Bloc 3G initial : une paire T5/RL-3, un pays, titulaire unique; "
            "crédits T2209/TP-772 traités séparément.",
        ),
    )


def lignes_resume_placement_etranger_2025(
    placement: PlacementEtranger2025,
    profil: ProfilPlacementEtranger2025,
):
    if not placement.present:
        return []

    def f(montant: Decimal) -> str:
        return f"{montant:,.2f} $".replace(",", " ").replace(".", ",")

    return [
        "",
        "PLACEMENT ÉTRANGER 2025 — BLOC 3G",
        f"Pays : {placement.pays}",
        f"Justificatif : {profil.source}",
        f"T5 15 / revenu étranger brut fédéral 12100 : {f(placement.revenu_brut_federal)}",
        f"RL-3 F / revenu étranger brut Québec 130 : {f(placement.revenu_brut_quebec)}",
        f"T5 16 / impôt étranger payé : {f(placement.impot_etranger_federal)}",
        f"RL-3 G / impôt étranger payé : {f(placement.impot_etranger_quebec)}",
        f"FSS Québec 446 sur le revenu de placement ligne 130 : {f(placement.cotisation_fss)}",
        "L'impôt étranger payé ne réduit pas le revenu brut et n'est pas une retenue canadienne.",
        "Crédits T2209/40500 et TP-772/409 non encore appliqués à cette étape.",
        "Montants des feuillets déjà en CAD; aucune conversion implicite.",
        "Obligations T1135/TP-1079.8.BE vérifiées séparément avant confirmation.",
    ]


@dataclass(frozen=True)
class ProfilCreditImpotEtranger2025:
    """Crédits étrangers confirmés à partir des formulaires officiels.

    Cette version ne reconstitue pas automatiquement T2209 ni TP-772.
    Les montants doivent provenir des formulaires 2025 vérifiés.
    """

    credit_federal_40500: Decimal = ZERO
    credit_quebec_409: Decimal = ZERO
    source_t2209: str = ""
    source_tp772: str = ""
    confirme: bool = False


@dataclass(frozen=True)
class CreditImpotEtranger2025:
    ligne_40500: Decimal = ZERO
    ligne_409: Decimal = ZERO
    present: bool = False


def valider_profil_credit_impot_etranger_2025(
    profil: ProfilCreditImpotEtranger2025,
    placement: PlacementEtranger2025,
) -> ProfilCreditImpotEtranger2025:
    if not isinstance(profil, ProfilCreditImpotEtranger2025):
        raise ValueError("Profil de crédit pour impôt étranger invalide.")
    if type(profil.confirme) is not bool:
        raise ValueError("La confirmation du crédit étranger doit être booléenne.")
    if not isinstance(profil.source_t2209, str) or not isinstance(
        profil.source_tp772, str
    ):
        raise ValueError("Les sources T2209 et TP-772 doivent être du texte.")

    _valider_montant(profil.credit_federal_40500, "Crédit fédéral 40500")
    _valider_montant(profil.credit_quebec_409, "Crédit Québec 409")

    if not placement.present:
        if profil != ProfilCreditImpotEtranger2025():
            raise ValueError(
                "Un crédit pour impôt étranger ne peut pas être confirmé sans revenu étranger."
            )
        return profil

    if not profil.confirme:
        raise ValueError(
            "Confirmez les montants 2025 calculés sur T2209 et TP-772."
        )
    if not profil.source_t2209.strip() or not profil.source_tp772.strip():
        raise ValueError(
            "Les références du T2209 et du TP-772 vérifiés sont obligatoires."
        )

    # Garde-fous certains, sans reproduire ici l'intégralité des formulaires.
    if profil.credit_federal_40500 > placement.impot_etranger_federal:
        raise ValueError(
            "Le crédit fédéral 40500 ne peut pas dépasser l'impôt étranger payé."
        )

    maximum_quebec_apres_federal = max(
        ZERO,
        placement.impot_etranger_quebec - profil.credit_federal_40500,
    )
    if profil.credit_quebec_409 > maximum_quebec_apres_federal:
        raise ValueError(
            "Le crédit Québec 409 non commercial ne peut pas dépasser "
            "l'impôt étranger payé moins le crédit fédéral accordé."
        )

    return profil


def consolider_credit_impot_etranger_2025(
    placement: PlacementEtranger2025,
    profil: ProfilCreditImpotEtranger2025,
) -> CreditImpotEtranger2025:
    valider_profil_credit_impot_etranger_2025(profil, placement)
    if not placement.present:
        return CreditImpotEtranger2025()

    return CreditImpotEtranger2025(
        ligne_40500=profil.credit_federal_40500,
        ligne_409=profil.credit_quebec_409,
        present=True,
    )


def appliquer_credit_impot_etranger_2025(
    federal,
    quebec,
    credit: CreditImpotEtranger2025,
):
    """Applique seulement les montants confirmés des formulaires 2025.

    Les crédits sont non remboursables : chacun est limité à l'impôt encore
    disponible dans sa juridiction.
    """
    if not isinstance(credit, CreditImpotEtranger2025):
        raise ValueError("Résultat de crédit étranger invalide.")
    if not credit.present:
        return federal, quebec

    _valider_montant(credit.ligne_40500, "Crédit fédéral 40500")
    _valider_montant(credit.ligne_409, "Crédit Québec 409")

    federal_apres = replace(
        federal,
        impot_federal_de_base=max(
            ZERO, federal.impot_federal_de_base - credit.ligne_40500
        ),
    )
    quebec_apres = replace(
        quebec,
        impot_quebec_preliminaire=max(
            ZERO, quebec.impot_quebec_preliminaire - credit.ligne_409
        ),
    )
    return federal_apres, quebec_apres


def lignes_resume_credit_impot_etranger_2025(
    credit: CreditImpotEtranger2025,
    profil: ProfilCreditImpotEtranger2025,
):
    if not credit.present:
        return []

    def f(montant: Decimal) -> str:
        return f"{montant:,.2f} $".replace(",", " ").replace(".", ",")

    return [
        "",
        "CRÉDITS POUR IMPÔT ÉTRANGER 2025 — BLOC 3G",
        f"T2209 vérifié : {profil.source_t2209}",
        f"Fédéral 40500 confirmé : {f(credit.ligne_40500)}",
        f"TP-772 vérifié : {profil.source_tp772}",
        f"Québec 409 confirmé : {f(credit.ligne_409)}",
        "Crédits non remboursables, limités à l'impôt disponible.",
        "Le moteur ne reconstitue pas encore automatiquement l'intégralité de T2209/TP-772.",
    ]
