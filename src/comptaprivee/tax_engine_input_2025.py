"""Consolidation des données fiscales validées pour le moteur 2025.

Cette étape construit une base fiscale cohérente à partir du dossier
verrouillé, sans additionner deux fois les mêmes renseignements T4 / RL-1.

Important :
- le revenu T4 case 14 et le revenu RL-1 case A sont conservés séparément;
- une différence entre ces deux revenus est permise, car certaines prestations
  peuvent être imposables uniquement au Québec;
- les cotisations et gains qui décrivent le même renseignement sur les deux
  feuillets sont comparés avant d'être acceptés;
- aucun impôt final n'est calculé dans ce module.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import (
    EI_MAX_QUEBEC_2025,
    QPP_BA_MAX_EMPLOYEE_2025,
    QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025,
)
from .tax_validated_case import DossierFiscalValide


ZERO = Decimal("0")
TOLERANCE_CENT = Decimal("0.01")


@dataclass(frozen=True)
class BaseFiscaleEmploi2025:
    client: str
    annee_fiscale: int
    province: str
    revenu_emploi_federal: Decimal
    revenu_emploi_quebec: Decimal
    impot_federal_retenu: Decimal
    impot_quebec_retenu: Decimal
    rrq_base_premiere_supplementaire: Decimal
    rrq_deuxieme_supplementaire: Decimal
    assurance_emploi: Decimal
    gains_assurables_ae: Decimal
    gains_admissibles_rrq: Decimal
    rqap: Decimal
    gains_assurables_rqap: Decimal
    nombre_t4: int
    nombre_rl1: int
    avertissements: tuple[str, ...]
    feuillets_emploi: tuple[tuple[str, str, tuple[tuple[str, Decimal], ...]], ...] = ()


def _valeurs(
    dossier: DossierFiscalValide,
    type_document: str,
    case: str,
) -> tuple[Decimal, ...]:
    return tuple(
        donnee.valeur_validee
        for donnee in dossier.donnees_validees
        if (
            donnee.type_document == type_document
            and donnee.case == case
        )
    )


def _total_optionnel(
    dossier: DossierFiscalValide,
    type_document: str,
    case: str,
) -> Decimal | None:
    valeurs = _valeurs(
        dossier,
        type_document,
        case,
    )

    if not valeurs:
        return None

    return sum(valeurs, ZERO)


def _total_requis(
    dossier: DossierFiscalValide,
    type_document: str,
    case: str,
) -> Decimal:
    total = _total_optionnel(
        dossier,
        type_document,
        case,
    )

    if total is None:
        raise ValueError(
            f"Donnée fiscale requise manquante : "
            f"{type_document} case {case}."
        )

    return total


def _verifier_correspondance(
    nom: str,
    valeur_t4: Decimal,
    valeur_rl1: Decimal,
) -> None:
    if abs(valeur_t4 - valeur_rl1) > TOLERANCE_CENT:
        raise ValueError(
            f"Incohérence T4 / RL-1 pour {nom} : "
            f"T4={valeur_t4} ; RL-1={valeur_rl1}."
        )


def _paire_optionnelle(
    dossier: DossierFiscalValide,
    case_t4: str,
    case_rl1: str,
    nom: str,
) -> Decimal:
    valeur_t4 = _total_optionnel(
        dossier,
        "T4",
        case_t4,
    )
    valeur_rl1 = _total_optionnel(
        dossier,
        "RL-1",
        case_rl1,
    )

    if valeur_t4 is None and valeur_rl1 is None:
        return ZERO

    if valeur_t4 is None or valeur_rl1 is None:
        raise ValueError(
            f"{nom} doit être présent sur les deux feuillets "
            f"(T4 case {case_t4} et RL-1 case {case_rl1}) "
            "ou absent des deux."
        )

    _verifier_correspondance(
        nom,
        valeur_t4,
        valeur_rl1,
    )

    return valeur_rl1


def _documents_uniques(
    dossier: DossierFiscalValide,
    type_document: str,
) -> set[str]:
    return {
        str(donnee.document)
        for donnee in dossier.donnees_validees
        if donnee.type_document == type_document
    }


def consolider_base_fiscale_emploi_2025(
    dossier: DossierFiscalValide,
) -> BaseFiscaleEmploi2025:
    """Prépare les entrées validées d'un dossier d'emploi Québec 2025."""
    if dossier.annee_fiscale != 2025:
        raise ValueError(
            "Le moteur de consolidation actuel accepte uniquement "
            "l'année fiscale 2025."
        )

    if dossier.province.strip().lower() not in {
        "québec",
        "quebec",
    }:
        raise ValueError(
            "Le moteur de consolidation actuel accepte uniquement "
            "les dossiers du Québec."
        )

    documents_t4 = _documents_uniques(
        dossier,
        "T4",
    )
    documents_rl1 = _documents_uniques(
        dossier,
        "RL-1",
    )

    if any(d.type_document == "T4" and d.case in {"16", "16A"}
           and d.valeur_validee != ZERO for d in dossier.donnees_validees):
        raise ValueError("RPC présent sur un T4 : RC381 hors périmètre, RRQ seulement.")
    feuillets = ()
    if len(documents_t4) > 1 or len(documents_rl1) > 1:
        feuillets = _verifier_feuillets_multiples(dossier, documents_t4, documents_rl1)

    if not documents_t4:
        raise ValueError(
            "Aucun T4 validé n'est présent dans le dossier."
        )

    if not documents_rl1:
        raise ValueError(
            "Aucun RL-1 validé n'est présent dans le dossier."
        )

    # Revenus distincts : on NE les compare PAS automatiquement.
    # Une différence T4-14 / RL-1-A peut être légitime au Québec.
    revenu_federal = _total_requis(
        dossier,
        "T4",
        "14",
    )
    revenu_quebec = _total_requis(
        dossier,
        "RL-1",
        "A",
    )

    impot_federal_retenu = _total_requis(
        dossier,
        "T4",
        "22",
    )
    impot_quebec_retenu = _total_requis(
        dossier,
        "RL-1",
        "E",
    )

    rrq_t4 = _total_requis(
        dossier,
        "T4",
        "17",
    )
    rrq_rl1 = _total_requis(
        dossier,
        "RL-1",
        "B.A",
    )
    _verifier_correspondance(
        "cotisations RRQ de base et première supplémentaire",
        rrq_t4,
        rrq_rl1,
    )

    rrq_deuxieme = _paire_optionnelle(
        dossier,
        "17A",
        "B.B",
        "deuxième cotisation supplémentaire RRQ",
    )

    ae_t4 = _total_requis(
        dossier,
        "T4",
        "18",
    )
    ae_rl1 = _total_requis(
        dossier,
        "RL-1",
        "C",
    )
    _verifier_correspondance(
        "cotisations d'assurance-emploi",
        ae_t4,
        ae_rl1,
    )

    gains_ae = _total_requis(
        dossier,
        "T4",
        "24",
    )

    gains_rrq_t4 = _total_requis(
        dossier,
        "T4",
        "26",
    )
    gains_rrq_rl1 = _total_requis(
        dossier,
        "RL-1",
        "G",
    )
    _verifier_correspondance(
        "gains admissibles au RRQ",
        gains_rrq_t4,
        gains_rrq_rl1,
    )

    rqap_t4 = _total_requis(
        dossier,
        "T4",
        "55",
    )
    rqap_rl1 = _total_requis(
        dossier,
        "RL-1",
        "H",
    )
    _verifier_correspondance(
        "cotisations au RQAP",
        rqap_t4,
        rqap_rl1,
    )

    gains_rqap_t4 = _total_requis(
        dossier,
        "T4",
        "56",
    )
    gains_rqap_rl1 = _total_requis(
        dossier,
        "RL-1",
        "I",
    )
    _verifier_correspondance(
        "gains assurables au RQAP",
        gains_rqap_t4,
        gains_rqap_rl1,
    )

    avertissements: list[str] = []

    if abs(revenu_federal - revenu_quebec) > TOLERANCE_CENT:
        avertissements.append(
            "Le revenu d'emploi fédéral (T4 case 14) diffère "
            "du revenu d'emploi Québec (RL-1 case A). Cette différence "
            "peut être légitime et doit rester séparée dans le calcul."
        )

    if rrq_rl1 > QPP_BA_MAX_EMPLOYEE_2025:
        avertissements.append(
            "Les cotisations RRQ B.A dépassent le maximum employé "
            "2025; vérifier une possible cotisation excédentaire ou "
            "plusieurs employeurs."
        )

    if rrq_deuxieme > QPP_SECOND_ADDITIONAL_MAX_EMPLOYEE_2025:
        avertissements.append(
            "Les cotisations RRQ B.B dépassent le maximum employé "
            "2025; vérifier une possible cotisation excédentaire."
        )

    if ae_t4 > EI_MAX_QUEBEC_2025:
        avertissements.append(
            "Les cotisations d'assurance-emploi dépassent le maximum "
            "Québec 2025; vérifier une possible cotisation excédentaire."
        )

    return BaseFiscaleEmploi2025(
        client=dossier.client,
        annee_fiscale=dossier.annee_fiscale,
        province=dossier.province,
        revenu_emploi_federal=revenu_federal,
        revenu_emploi_quebec=revenu_quebec,
        impot_federal_retenu=impot_federal_retenu,
        impot_quebec_retenu=impot_quebec_retenu,
        rrq_base_premiere_supplementaire=rrq_rl1,
        rrq_deuxieme_supplementaire=rrq_deuxieme,
        assurance_emploi=ae_t4,
        gains_assurables_ae=gains_ae,
        gains_admissibles_rrq=gains_rrq_rl1,
        rqap=rqap_rl1,
        gains_assurables_rqap=gains_rqap_rl1,
        nombre_t4=len(documents_t4),
        nombre_rl1=len(documents_rl1),
        avertissements=tuple(avertissements),
        feuillets_emploi=feuillets,
    )


def _verifier_feuillets_multiples(dossier, documents_t4, documents_rl1):
    """Une source par feuillet; appariement comptable, jamais déduit du salaire."""
    if len(documents_t4) != len(documents_rl1):
        raise ValueError("7A exige autant de T4 que de RL-1, un de chaque par employeur.")
    requis = {"T4": {"14", "17", "18", "22", "24", "26", "55", "56"},
              "RL-1": {"A", "B.A", "C", "E", "G", "H", "I"}}
    permis = {"T4": requis["T4"] | {"17A", "16", "16A", "20", "44"},
              "RL-1": requis["RL-1"] | {"B.B", "D", "F", "J", "211"}}
    groupes = {}
    sources = {}
    for d in dossier.donnees_validees:
        if d.type_document not in requis:
            raise ValueError("7A : seuls les feuillets T4/RL-1 ordinaires sont pris en charge.")
        cle = (str(d.document).replace("\\", "/").casefold(), d.type_document)
        sources.setdefault(cle, str(d.document))
        valeurs = groupes.setdefault(cle, {})
        if d.case in valeurs:
            raise ValueError("7A : doublon de case ou de feuillet.")
        montant = d.valeur_validee
        if not isinstance(montant, Decimal) or not montant.is_finite() or montant < ZERO:
            raise ValueError("7A : montant de feuillet invalide.")
        if d.case not in permis[d.type_document] and montant:
            raise ValueError(f"7A : {d.type_document} case {d.case} hors périmètre.")
        valeurs[d.case] = montant
    empreintes = set()
    signatures = {"T4": [], "RL-1": []}
    paires = {"T4": ("17", "17A", "18", "26", "55", "56"),
              "RL-1": ("B.A", "B.B", "C", "G", "H", "I")}
    for (document, type_doc), valeurs in groupes.items():
        if not requis[type_doc] <= valeurs.keys():
            raise ValueError(f"7A : cases requises manquantes sur {document}.")
        empreinte = (type_doc, tuple(sorted((c, v) for c, v in valeurs.items() if v)))
        if empreinte in empreintes:
            raise ValueError("7A : doublon potentiel de feuillet (montants identiques); vérifier les originaux.")
        empreintes.add(empreinte)
        signatures[type_doc].append(tuple(valeurs.get(c, ZERO) for c in paires[type_doc]))
        if type_doc == "T4" and valeurs["26"] > Decimal("81200"):
            raise ValueError("7A : case 26 supérieure à 81 200 $ par feuillet; vérifier le T4.")
    if sorted(signatures["T4"]) != sorted(signatures["RL-1"]):
        raise ValueError("7A : correspondance des cotisations/gains par feuillet T4/RL-1 incohérente.")
    return tuple((sources[(doc, typ)], typ, tuple(sorted(vals.items()))) for (doc, typ), vals in sorted(groupes.items()))
