"""Frais de scolarité et d'examen 2025 - profil Québec simple.

Portée volontairement limitée :
- frais admissibles payés pour 2025 seulement;
- aucun report d'années antérieures;
- aucun transfert à un parent ou grand-parent;
- crédit canadien pour la formation via le profil dédié 5C;
- pièces justificatives et admissibilité déjà vérifiées;
- résident du Québec/Canada dans le profil simple de ComptaPrivée.

Références de calcul visées :
- fédéral : annexe 11, ligne 32300;
- Québec : annexe T, ligne 398.

Cette première version calcule les crédits non remboursables associés aux
montants admissibles validés. Elle ne calcule pas encore les reports, les
transferts. Le crédit formation est intégré séparément en 5C.
"""

from dataclasses import dataclass, replace
from decimal import Decimal

from .tax_training_credit_2025 import Formation2025, credit_formation_2025, valider_formation_2025
from .tax_federal_top_up_2025 import valider_scolarite_sans_report_2025
from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025
from .tax_rules_2025 import arrondir_cent


ZERO = Decimal("0")
CENT_DOLLARS = Decimal("100")
TAUX_CREDIT_FEDERAL_SCOLARITE_2025 = Decimal("0.145")
TAUX_CREDIT_QUEBEC_SCOLARITE_2025 = Decimal("0.08")


@dataclass(frozen=True)
class FraisScolarite2025:
    """Montants de scolarité/examen admissibles déjà vérifiés pour 2025."""

    montant_admissible_federal: Decimal = ZERO
    montant_admissible_quebec: Decimal = ZERO
    source_federale: str = ""
    source_quebec: str = ""

    valide_par_comptable: bool = False
    piece_federale_confirmee: bool = False
    recu_officiel_quebec_confirme: bool = False
    seuil_100_confirme: bool = False
    remboursements_soustraits: bool = False
    frais_2025_uniquement: bool = False

    aucun_report_anterieur: bool = False
    aucun_transfert: bool = False
    credit_canadien_formation_non_reclame: bool = False
    profil_resident_quebec_simple: bool = False
    formation: Formation2025 = Formation2025()

    @property
    def montant_net_federal(self) -> Decimal:
        return self.montant_admissible_federal - credit_formation_2025(self.formation)

    @property
    def montant_net_quebec(self) -> Decimal:
        return self.montant_admissible_quebec - credit_formation_2025(self.formation)



def aucun_frais_scolarite_2025() -> FraisScolarite2025:
    return FraisScolarite2025()


def valider_frais_scolarite_2025(
    frais: FraisScolarite2025,
) -> FraisScolarite2025:
    for nom in ("montant_admissible_federal", "montant_admissible_quebec"):
        montant = getattr(frais, nom)
        if not isinstance(montant, Decimal) or not montant.is_finite():
            raise ValueError(f"{nom} doit être un Decimal fini.")
    valider_formation_2025(frais.formation)
    ccf = credit_formation_2025(frais.formation)
    if frais.formation.frais_canadiens and frais.formation.frais_canadiens > frais.montant_admissible_federal:
        raise ValueError("Les frais canadiens formation doivent être inclus dans les frais fédéraux bruts.")
    if ccf and ccf > frais.montant_admissible_quebec:
        raise ValueError("CCF supérieur aux frais Québec : combinaison hors profil 5C, validation spécialisée nécessaire.")
    if ccf and frais.credit_canadien_formation_non_reclame:
        raise ValueError("Confirmation contradictoire : formation réclamée et non réclamée.")
    fed = frais.montant_admissible_federal
    qc = frais.montant_admissible_quebec

    if fed < ZERO:
        raise ValueError(
            "Le montant admissible fédéral des frais de scolarité "
            "ne peut pas être négatif."
        )

    if qc < ZERO:
        raise ValueError(
            "Le montant admissible Québec des frais de scolarité "
            "ne peut pas être négatif."
        )

    if fed == ZERO and qc == ZERO:
        return frais

    if ZERO < fed <= CENT_DOLLARS:
        raise ValueError(
            "Les frais fédéraux admissibles doivent dépasser 100 $ "
            "par établissement pour l'année."
        )

    if ZERO < qc <= CENT_DOLLARS:
        raise ValueError(
            "Le total des frais de scolarité ou d'examen du Québec "
            "doit dépasser 100 $ pour l'année."
        )

    if not frais.valide_par_comptable:
        raise ValueError(
            "Les frais de scolarité doivent être validés par le comptable."
        )

    if fed > ZERO and not frais.piece_federale_confirmee:
        raise ValueError(
            "Une pièce fédérale admissible (T2202, TL11 ou reçu officiel) "
            "doit être confirmée."
        )

    if qc > ZERO and not frais.recu_officiel_quebec_confirme:
        raise ValueError(
            "Le reçu officiel Québec des frais admissibles doit être confirmé."
        )

    if not frais.seuil_100_confirme:
        raise ValueError(
            "Le respect du seuil minimal de plus de 100 $ doit être confirmé."
        )

    if not frais.remboursements_soustraits:
        raise ValueError(
            "Les remboursements non inclus dans le revenu doivent être "
            "soustraits avant le calcul."
        )

    if not frais.frais_2025_uniquement:
        raise ValueError(
            "Cette version accepte uniquement les frais admissibles "
            "payés pour 2025."
        )

    if not frais.aucun_report_anterieur:
        raise ValueError(
            "Cette version n'accepte pas encore les montants reportés "
            "d'années antérieures."
        )

    if not frais.aucun_transfert:
        raise ValueError(
            "Cette version n'accepte pas encore les transferts de frais "
            "de scolarité à une autre personne."
        )

    if not frais.credit_canadien_formation_non_reclame and not ccf:
        raise ValueError(
            "Cette version exige qu'aucun crédit canadien pour la formation "
            "ne soit réclamé sur les mêmes frais."
        )

    if not frais.profil_resident_quebec_simple:
        raise ValueError(
            "Cette version accepte uniquement le profil résident du Québec "
            "et du Canada pris en charge par ComptaPrivée."
        )

    if fed > ZERO and not frais.source_federale.strip():
        raise ValueError(
            "La source fédérale des frais de scolarité est obligatoire."
        )

    if qc > ZERO and not frais.source_quebec.strip():
        raise ValueError(
            "La source Québec des frais de scolarité est obligatoire."
        )

    return frais


def credit_federal_frais_scolarite_2025(
    frais: FraisScolarite2025,
) -> Decimal:
    valider_frais_scolarite_2025(frais)
    return arrondir_cent(
        frais.montant_net_federal
        * TAUX_CREDIT_FEDERAL_SCOLARITE_2025
    )


def credit_quebec_frais_scolarite_2025(
    frais: FraisScolarite2025,
) -> Decimal:
    valider_frais_scolarite_2025(frais)
    return arrondir_cent(
        frais.montant_net_quebec
        * TAUX_CREDIT_QUEBEC_SCOLARITE_2025
    )


def appliquer_credit_federal_frais_scolarite_2025(
    impot: ImpotFederalPreliminaire2025,
    frais: FraisScolarite2025,
    *,
    base_ligne105: Decimal | None = None,
) -> ImpotFederalPreliminaire2025:
    credit = credit_federal_frais_scolarite_2025(frais)

    if credit == ZERO:
        return impot

    if base_ligne105 is not None:
        valider_scolarite_sans_report_2025(
            frais.montant_net_federal, impot.revenu_imposable,
            impot.impot_brut, base_ligne105,
        )
    elif credit > impot.impot_federal_de_base:
        raise ValueError(
            "Une partie du montant fédéral de scolarité devrait être "
            "reportée à une année future. Le report est hors profil "
            "dans cette version."
        )

    nouvelles_limitations = []
    for texte in impot.limitations:
        if texte == (
            "Aucun crédit pour handicap, frais médicaux ou scolarité."
        ):
            nouvelles_limitations.append(
                "Aucun crédit pour handicap ou frais médicaux."
            )
        elif texte == "Aucun crédit pour handicap ou scolarité.":
            nouvelles_limitations.append(
                "Aucun crédit pour handicap."
            )
        else:
            nouvelles_limitations.append(texte)

    nouvelles_limitations.append(
        "Crédit fédéral pour frais de scolarité admissibles inclus."
    )

    return replace(
        impot,
        impot_federal_de_base=max(
            arrondir_cent(
                impot.impot_federal_de_base - credit
            ),
            ZERO,
        ),
        limitations=tuple(nouvelles_limitations),
    )


def appliquer_credit_quebec_frais_scolarite_2025(
    impot: ImpotQuebecPreliminaire2025,
    frais: FraisScolarite2025,
) -> ImpotQuebecPreliminaire2025:
    credit = credit_quebec_frais_scolarite_2025(frais)

    if credit == ZERO:
        return impot

    if credit > impot.impot_quebec_preliminaire:
        raise ValueError(
            "Une partie du montant Québec de scolarité ou d'examen "
            "devrait être reportée à une année future. Le report est "
            "hors profil dans cette version."
        )

    remplacements = {
        "Aucun crédit handicap, médical, scolarité ou don.":
            "Aucun crédit handicap, médical ou don.",
        "Aucun crédit handicap, médical ou scolarité.":
            "Aucun crédit handicap ou médical.",
        "Aucun crédit handicap, scolarité ou don.":
            "Aucun crédit handicap ou don.",
        "Aucun crédit handicap ou scolarité.":
            "Aucun crédit handicap.",
    }

    nouvelles_limitations = [
        remplacements.get(texte, texte)
        for texte in impot.limitations
    ]
    nouvelles_limitations.append(
        "Crédit Québec pour frais de scolarité ou d'examen admissibles inclus."
    )

    return replace(
        impot,
        impot_quebec_preliminaire=max(
            arrondir_cent(
                impot.impot_quebec_preliminaire - credit
            ),
            ZERO,
        ),
        limitations=tuple(nouvelles_limitations),
    )
