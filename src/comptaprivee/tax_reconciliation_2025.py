"""Rapprochement fiscal préliminaire Canada + Québec 2025.

Cette étape rapproche :
- l'impôt fédéral de base déjà calculé;
- l'abattement remboursable du Québec de 16,5 %;
- l'impôt Québec préliminaire;
- les retenues d'impôt déjà prélevées sur le T4 et le RL-1.

Le résultat est une ESTIMATION DE BASE pour le profil emploi Québec simple.
Il ne constitue pas une déclaration fiscale complète et ne doit pas être
transmis à l'ARC ou à Revenu Québec sans validation comptable finale.

Sont notamment hors profil : crédits familiaux, médicaux, études, dons,
assurance médicaments, cotisations excédentaires, CNESST/SAAQ, revenus
autonomes, plusieurs employeurs et autres situations particulières.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tax_capital_gains_2025 import GainsCapital2025
from .tax_dividend_income_2025 import Dividendes2025
from .tax_interest_income_2025 import Interets2025
from .tax_replacement_benefits_2025 import PrestationsRemplacement2025
from .tax_rrsp_withdrawals_2025 import Retraits2025
from .tax_pension_income_2025 import RevenusPensions2025
from .tax_old_age_security_2025 import PrestationsPsv2025
from .tax_cpp_qpp_benefits_2025 import PrestationsRrqRpc2025
from .tax_employment_insurance_2025 import PrestationsAe2025
from .tax_parental_benefits_2025 import PrestationsRqap2025
from .tax_engine_input_2025 import BaseFiscaleEmploi2025
from .tax_federal_2025 import ImpotFederalPreliminaire2025
from .tax_quebec_2025 import ImpotQuebecPreliminaire2025
from .tax_rules_2025 import QUEBEC_ABATEMENT_RATE, arrondir_cent


ZERO = Decimal("0")


@dataclass(frozen=True)
class RapprochementFiscal2025:
    client: str
    annee_fiscale: int
    province: str

    impot_federal_de_base: Decimal
    abattement_quebec: Decimal
    impot_federal_apres_abattement: Decimal

    impot_quebec_preliminaire: Decimal
    impot_total_preliminaire: Decimal

    retenue_federale: Decimal
    retenue_quebec: Decimal
    retenues_totales: Decimal

    remboursement_estime: Decimal
    solde_estime: Decimal
    resultat: str

    statut: str
    limitations: tuple[str, ...]
    cotisation_assurance_medicaments: Decimal = ZERO
    remboursement_rrq_excedentaire: Decimal = ZERO
    remboursement_ae_excedentaire: Decimal = ZERO
    remboursement_rqap_excedentaire: Decimal = ZERO
    remboursements_cotisations_totaux: Decimal = ZERO


def _verifier_coherence(
    base: BaseFiscaleEmploi2025,
    federal: ImpotFederalPreliminaire2025,
    quebec: ImpotQuebecPreliminaire2025,
) -> None:
    if base.client != federal.client or base.client != quebec.client:
        raise ValueError(
            "Les modules fiscal, fédéral et Québec ne concernent "
            "pas le même client."
        )

    if (
        base.annee_fiscale != federal.annee_fiscale
        or base.annee_fiscale != quebec.annee_fiscale
    ):
        raise ValueError(
            "Les modules n'utilisent pas la même année fiscale."
        )

    if base.annee_fiscale != 2025:
        raise ValueError(
            "Cette version du rapprochement accepte uniquement 2025."
        )

    if base.province.strip().lower() not in {"québec", "quebec"}:
        raise ValueError(
            "L'abattement automatique de cette version exige "
            "un dossier Québec."
        )


def calculer_rapprochement_fiscal_2025(
    base: BaseFiscaleEmploi2025,
    federal: ImpotFederalPreliminaire2025,
    quebec: ImpotQuebecPreliminaire2025,
    cotisation_assurance_medicaments: Decimal = ZERO,
    remboursement_rrq_excedentaire: Decimal = ZERO,
    remboursement_ae_excedentaire: Decimal = ZERO,
    remboursement_rqap_excedentaire: Decimal = ZERO,
    cotisations_excedentaires_verifiees: bool = False,
    prestations_rqap: PrestationsRqap2025 = PrestationsRqap2025(),
    prestations_ae: PrestationsAe2025 = PrestationsAe2025(),
    prestations_rrq_rpc: PrestationsRrqRpc2025 = PrestationsRrqRpc2025(),
    prestations_psv: PrestationsPsv2025 = PrestationsPsv2025(),
    pensions: RevenusPensions2025 = RevenusPensions2025(),
    capital: GainsCapital2025 = GainsCapital2025(),
    dividendes: Dividendes2025 = Dividendes2025(),
    interets: Interets2025 = Interets2025(),
    remplacement: PrestationsRemplacement2025 = PrestationsRemplacement2025(),
    retraits: Retraits2025 = Retraits2025(),
) -> RapprochementFiscal2025:
    """Calcule une estimation de base du remboursement ou du solde."""
    _verifier_coherence(base, federal, quebec)

    abattement = arrondir_cent(
        federal.impot_federal_de_base
        * QUEBEC_ABATEMENT_RATE
    )

    federal_apres_abattement = max(
        arrondir_cent(
            federal.impot_federal_de_base - abattement
        ),
        ZERO,
    )

    if cotisation_assurance_medicaments < ZERO:
        raise ValueError(
            "La cotisation d'assurance médicaments ne peut pas "
            "être négative."
        )

    for nom, montant in (
        ("remboursement RRQ", remboursement_rrq_excedentaire),
        (
            "remboursement assurance-emploi",
            remboursement_ae_excedentaire,
        ),
        ("remboursement RQAP", remboursement_rqap_excedentaire),
    ):
        if montant < ZERO:
            raise ValueError(
                f"Le {nom} ne peut pas être négatif."
            )

    remboursements_cotisations_totaux = arrondir_cent(
        remboursement_rrq_excedentaire
        + remboursement_ae_excedentaire
        + remboursement_rqap_excedentaire
    )

    impot_total = arrondir_cent(
        federal_apres_abattement
        + quebec.impot_quebec_preliminaire
        + cotisation_assurance_medicaments
        + prestations_rqap.cotisation_fss
        + prestations_ae.cotisation_fss + prestations_ae.recuperation
        + prestations_rrq_rpc.cotisation_fss + prestations_psv.recuperation + pensions.cotisation_fss + retraits.cotisation_fss + interets.cotisation_fss + dividendes.cotisation_fss + capital.cotisation_fss
    )

    retenues_totales = arrondir_cent(
        base.impot_federal_retenu
        + base.impot_quebec_retenu
        + prestations_rqap.retenue_federale + prestations_rqap.retenue_quebec
        + prestations_ae.retenue_federale + prestations_ae.retenue_quebec
        + prestations_rrq_rpc.retenue_federale + prestations_rrq_rpc.retenue_quebec
        + prestations_psv.retenue_federale + prestations_psv.retenue_quebec
        + pensions.retenue_federale + pensions.retenue_quebec + retraits.retenue_federale + retraits.retenue_quebec
    )

    difference = arrondir_cent(
        retenues_totales
        + remboursements_cotisations_totaux
        - impot_total
    )

    if difference > ZERO:
        remboursement = difference
        solde = ZERO
        resultat = "Remboursement estimé"
    elif difference < ZERO:
        remboursement = ZERO
        solde = abs(difference)
        resultat = "Solde estimé"
    else:
        remboursement = ZERO
        solde = ZERO
        resultat = "Équilibre estimé"

    credit_medical_inclus = (
        "Crédit fédéral pour frais médicaux admissibles inclus."
        in federal.limitations
        or "Crédit Québec pour frais médicaux admissibles inclus."
        in quebec.limitations
    )
    credit_scolarite_inclus = (
        "Crédit fédéral pour frais de scolarité admissibles inclus."
        in federal.limitations
        or (
            "Crédit Québec pour frais de scolarité ou d'examen "
            "admissibles inclus."
        )
        in quebec.limitations
    )
    credit_handicap_inclus = (
        "Crédit fédéral pour personnes handicapées inclus."
        in federal.limitations
        or (
            "Crédit Québec pour déficience grave et prolongée inclus."
            in quebec.limitations
        )
    )

    credit_personne_seule_inclus = (
        "Montant Québec pour personne vivant seule inclus à la ligne 361."
        in quebec.limitations
    )
    credit_conjoint_federal_inclus = (
        "Montant fédéral pour époux ou conjoint de fait ligne 30300 inclus."
        in federal.limitations
    )
    credit_personne_charge_federal_inclus = (
        "Montant fédéral pour personne à charge admissible "
        "ligne 30400 inclus."
        in federal.limitations
    )
    credit_aidant_30425_federal_inclus = (
        "Montant canadien pour aidant naturel ligne 30425 inclus."
        in federal.limitations
    )
    credit_accessibilite_domiciliaire_federal_inclus = (
        "Dépenses pour l'accessibilité domiciliaire ligne 31285 incluses."
        in federal.limitations
    )
    credit_achat_habitation_federal_inclus = (
        "Montant pour l'achat d'une habitation ligne 31270 inclus."
        in federal.limitations
    )
    credit_aidant_30450_federal_inclus = (
        "Montant canadien pour aidant naturel ligne 30450 inclus."
        in federal.limitations
    )
    credit_aidant_enfant_federal_inclus = (
        "Montant canadien pour aidant naturel enfant de moins de 18 ans "
        "ligne 30500 inclus."
        in federal.limitations
    )
    credit_familial_inclus = (
        credit_personne_seule_inclus
        or credit_conjoint_federal_inclus
        or credit_personne_charge_federal_inclus
        or credit_aidant_enfant_federal_inclus
        or credit_aidant_30425_federal_inclus
        or credit_aidant_30450_federal_inclus
    )
    credit_age_retraite_inclus = (
        "Montants Québec en raison de l\'âge ou pour revenus de retraite "
        "inclus à la ligne 361."
        in quebec.limitations
    )
    credit_age_pension_federal_inclus = (
        "Montant fédéral en raison de l'âge ligne 30100 inclus." in federal.limitations
    )

    credits_absents = []
    if not credit_familial_inclus:
        credits_absents.append("familial")
    if not credit_medical_inclus:
        credits_absents.append("médical")
    if not credit_scolarite_inclus:
        credits_absents.append("étude")
    if not credit_handicap_inclus:
        credits_absents.append("handicap")

    if not credits_absents:
        if (
            credit_conjoint_federal_inclus
            and credit_personne_seule_inclus
        ):
            limitation_credits = (
                "Crédits familiaux fédéral et Québec inclus."
            )
        elif (
            credit_personne_charge_federal_inclus
            and credit_personne_seule_inclus
        ):
            limitation_credits = (
                "Montant fédéral pour personne à charge admissible "
                "et crédit familial Québec inclus."
            )
        elif credit_conjoint_federal_inclus:
            limitation_credits = (
                "Montant fédéral pour époux ou conjoint de fait inclus."
            )
        elif credit_personne_charge_federal_inclus:
            limitation_credits = (
                "Montant fédéral pour personne à charge admissible inclus."
            )
        else:
            limitation_credits = (
                "Crédit familial Québec pour personne vivant seule inclus."
            )
    elif len(credits_absents) == 1:
        limitation_credits = f"Aucun crédit {credits_absents[0]}."
    elif len(credits_absents) == 2:
        limitation_credits = (
            f"Aucun crédit {credits_absents[0]} "
            f"ou {credits_absents[1]}."
        )
    else:
        limitation_credits = (
            "Aucun crédit "
            + ", ".join(credits_absents[:-1])
            + " ou "
            + credits_absents[-1]
            + "."
        )

    return RapprochementFiscal2025(
        client=base.client,
        annee_fiscale=base.annee_fiscale,
        province=base.province,
        impot_federal_de_base=federal.impot_federal_de_base,
        abattement_quebec=abattement,
        impot_federal_apres_abattement=federal_apres_abattement,
        impot_quebec_preliminaire=quebec.impot_quebec_preliminaire,
        impot_total_preliminaire=impot_total,
        retenue_federale=base.impot_federal_retenu + prestations_rqap.retenue_federale + prestations_ae.retenue_federale + prestations_rrq_rpc.retenue_federale + prestations_psv.retenue_federale + pensions.retenue_federale + retraits.retenue_federale,
        retenue_quebec=base.impot_quebec_retenu + prestations_rqap.retenue_quebec + prestations_ae.retenue_quebec + prestations_rrq_rpc.retenue_quebec + prestations_psv.retenue_quebec + pensions.retenue_quebec + retraits.retenue_quebec,
        retenues_totales=retenues_totales,
        remboursement_estime=remboursement,
        solde_estime=solde,
        resultat=resultat,
        statut="ESTIMATION DE BASE — validation comptable obligatoire",
        limitations=(
            ("Le calcul couvre le profil emploi Québec avec RQAP ordinaire 2025." if prestations_rqap.present
             else "Le calcul couvre le profil emploi Québec et AE ordinaire 2025." if prestations_ae.present
             else "RRQ/RPC ordinaire Québec 2025, avec ou sans emploi." if prestations_rrq_rpc.present
             else "PSV/suppléments ordinaires Québec 2025; récupération 42200 sans abattement, FSS nul." if prestations_psv.present
             else "Pensions domestiques ordinaires 2025, avec ou sans emploi; FSS sur la pension brute." if pensions.present
             else "Retraits REER et forfaits ordinaires 2025, avec ou sans emploi." if retraits.present
             else "Prestations T5007/RL-5 ordinaires, avec ou sans emploi; redressement 358 inclus." if remplacement.present
             else "Vente unique actions canadiennes 2025 : gain imposable 12700/139 et FSS; aucun report de perte." if capital.present
             else "Dividendes canadiens T5/RL-3 2025; crédits 40425/415 et FSS sur les montants réels inclus." if dividendes.present
             else "Intérêts canadiens documentés 2025, avec ou sans emploi; FSS 446 inclus." if interets.present
             else "Le calcul couvre uniquement le profil emploi Québec simple 2025."),
            "L'abattement Québec est calculé à 16,5 % de l'impôt fédéral de base.",
            ("Retenues T4/RL-1 et T4E/RL-6 incluses; FSS ligne 446 calculé." if prestations_rqap.present
             else "AE : retenues T4E incluses; récupération 42200 et FSS 446 ajoutés sans abattement." if prestations_ae.present
             else "Retenues RRQ/RPC incluses; FSS 446 ajouté sans abattement fédéral." if prestations_rrq_rpc.present
             else "Retenues T4A(OAS) 22/23 incluses une fois, distinctes de la récupération calculée." if prestations_psv.present
             else "Retenues pensions incluses une fois; FSS ajouté sans abattement fédéral." if pensions.present
             else "Retenues retraits incluses une fois; FSS ajouté sans abattement." if retraits.present
             else "Les retenues T4 et RL-1 sont comparées aux impôts préliminaires."),
            limitation_credits,
            *(
                (
                    "Montant fédéral pour époux ou conjoint de fait ligne 30300 inclus.",
                )
                if credit_conjoint_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant fédéral pour personne à charge admissible ligne 30400 inclus.",
                )
                if credit_personne_charge_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant canadien pour aidant naturel ligne 30425 inclus.",
                )
                if credit_aidant_30425_federal_inclus
                else ()
            ),
            *(
                (
                    "Dépenses pour l'accessibilité domiciliaire ligne 31285 incluses.",
                )
                if credit_accessibilite_domiciliaire_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant pour l'achat d'une habitation ligne 31270 inclus.",
                )
                if credit_achat_habitation_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant canadien pour aidant naturel ligne 30450 inclus.",
                )
                if credit_aidant_30450_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant canadien pour aidant naturel enfant de moins de 18 ans ligne 30500 inclus.",
                )
                if credit_aidant_enfant_federal_inclus
                else ()
            ),
            *(
                (
                    "Montant fédéral en raison de l'âge ligne 30100 inclus.",
                )
                if credit_age_pension_federal_inclus
                else ()
            ),
            *(
                (
                    "Montants Québec en raison de l\'âge ou pour revenus "
                    "de retraite inclus.",
                )
                if credit_age_retraite_inclus
                else ()
            ),
            *(
                (
                    "Cotisation au régime d'assurance médicaments "
                    "du Québec incluse.",
                )
                if cotisation_assurance_medicaments > ZERO
                else (
                    ("Aucune prime d'assurance médicaments; FSS RQAP inclus." if prestations_rqap.cotisation_fss
                     else "Aucune prime d'assurance médicaments; FSS AE inclus." if prestations_ae.cotisation_fss
                     else "Aucune prime d'assurance médicaments; FSS RRQ/RPC inclus." if prestations_rrq_rpc.cotisation_fss
                     else "Aucune prime d'assurance médicaments; FSS pensions inclus." if pensions.present
                     else "Aucune prime d'assurance médicaments; FSS retraits inclus." if retraits.present
                     else "Aucune prime d'assurance médicaments; FSS capital inclus." if capital.present
                     else "Aucune prime d'assurance médicaments; FSS dividendes inclus." if dividendes.present
                     else "Aucune prime d'assurance médicaments; FSS intérêts inclus." if interets.present
                     else "Aucune prime d'assurance médicaments ni contribution Québec additionnelle."),
                )
            ),
            *(
                (
                    "Remboursements de cotisations excédentaires "
                    "RRQ/AE/RQAP inclus.",
                )
                if remboursements_cotisations_totaux > ZERO
                else (
                    (
                        "Cotisations RRQ/AE/RQAP vérifiées : "
                        "aucun excédent remboursable selon le profil "
                        "standard supporté.",
                    )
                    if cotisations_excedentaires_verifiees
                    else (
                        "Aucun remboursement de cotisations "
                        "excédentaires RRQ/AE/RQAP.",
                    )
                )
            ),
            ("Aucun revenu autonome, autre placement ni location; une seule disposition en capital." if capital.present else "Aucun revenu autonome, autre placement, location ou gain en capital." if interets.present or dividendes.present else "Aucun revenu autonome, placement, location ou gain en capital."),
            "Aucun traitement avancé CNESST/SAAQ.",
            "Aucune transmission ARC ou Revenu Québec.",
        ),
        cotisation_assurance_medicaments=(
            cotisation_assurance_medicaments
        ),
        remboursement_rrq_excedentaire=(
            remboursement_rrq_excedentaire
        ),
        remboursement_ae_excedentaire=(
            remboursement_ae_excedentaire
        ),
        remboursement_rqap_excedentaire=(
            remboursement_rqap_excedentaire
        ),
        remboursements_cotisations_totaux=(
            remboursements_cotisations_totaux
        ),
    )
