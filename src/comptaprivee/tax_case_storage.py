"""Persistance locale des dossiers fiscaux validés."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any

from .tax_adjustments_2025 import (
    AjustementReer2025,
    valider_ajustement_reer_2025,
)
from .tax_union_dues_2025 import (
    CotisationsSyndicalesProfessionnelles2025,
    valider_cotisations_syndicales_2025,
)
from .tax_donations_2025 import (
    DonsBienfaisance2025,
    valider_dons_bienfaisance_2025,
)
from .tax_disability_2025 import (
    CreditDeficience2025,
    valider_credit_deficience_2025,
)
from .tax_drug_insurance_2025 import (
    AssuranceMedicamentsQuebec2025,
    valider_assurance_medicaments_2025,
)
from .tax_contribution_overpayments_2025 import (
    CotisationsExcedentaires2025,
    valider_cotisations_excedentaires_2025,
)
from .tax_age_retirement_2025 import (
    MontantsAgeRetraite2025,
    valider_montants_age_retraite_2025,
)
from .tax_federal_age_pension_2025 import (
    CreditsFederauxAgePension2025,
    valider_credits_federaux_age_pension_2025,
)
from .tax_federal_spouse_2025 import (
    MontantConjointFederal2025,
    valider_montant_conjoint_federal_2025,
)
from .tax_federal_eligible_dependant_2025 import (
    MontantPersonneChargeAdmissibleFederal2025,
    valider_montant_personne_charge_admissible_federal_2025,
)
from .tax_living_alone_2025 import (
    PersonneVivantSeule2025,
    valider_personne_vivant_seule_2025,
)
from .tax_medical_expenses_2025 import (
    FraisMedicaux2025,
    valider_frais_medicaux_2025,
)
from .tax_tuition_2025 import (
    FraisScolarite2025,
    valider_frais_scolarite_2025,
)
from .tax_estimation_2025 import EstimationFiscale2025
from .tax_field_validation import (
    DonneeFiscaleValidee,
    STATUT_CORRIGE_VALIDE,
    STATUT_VALIDE,
)
from .tax_validated_case import DossierFiscalValide

SCHEMA_VERSION = 1

# Racine stable du projet, indépendante du dossier courant.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOSSIERS_FISCAUX_DIR = (
    PROJECT_ROOT / "data" / "dossiers_fiscaux"
)
STATUTS_VALIDATION_AUTORISES = {STATUT_VALIDE, STATUT_CORRIGE_VALIDE}


@dataclass(frozen=True)
class ResumeEstimationSauvegardee:
    resultat: str
    montant: Decimal
    impot_total_preliminaire: Decimal
    retenues_totales: Decimal


@dataclass(frozen=True)
class DossierFiscalEnregistre:
    chemin: Path
    dossier: DossierFiscalValide
    sauvegarde_le: str
    estimation: ResumeEstimationSauvegardee | None
    rapport_pdf: Path | None
    documents_manquants: tuple[Path, ...]
    ajustement_reer: AjustementReer2025
    cotisations_syndicales: CotisationsSyndicalesProfessionnelles2025
    dons_bienfaisance: DonsBienfaisance2025
    frais_medicaux: FraisMedicaux2025
    frais_scolarite: FraisScolarite2025
    credit_deficience: CreditDeficience2025
    assurance_medicaments: AssuranceMedicamentsQuebec2025
    cotisations_excedentaires: CotisationsExcedentaires2025
    personne_vivant_seule: PersonneVivantSeule2025
    montants_age_retraite: MontantsAgeRetraite2025
    credits_federaux_age_pension: CreditsFederauxAgePension2025
    montant_conjoint_federal: MontantConjointFederal2025
    personne_charge_admissible_federale: MontantPersonneChargeAdmissibleFederal2025


def _nom_securise(valeur: str) -> str:
    texte = re.sub(r"[^\w-]+", "_", valeur.strip(), flags=re.UNICODE)
    texte = re.sub(r"_+", "_", texte).strip("_")
    return texte or "client"


def nom_fichier_dossier_fiscal(dossier: DossierFiscalValide) -> str:
    return f"Dossier_Fiscal_{dossier.annee_fiscale}_{_nom_securise(dossier.client)}.json"


def _chemin_vers_stockage(chemin: Path) -> str:
    valeur = Path(chemin)

    if valeur.is_absolute():
        absolu = valeur
    else:
        absolu = PROJECT_ROOT / valeur

    try:
        absolu_resolu = absolu.resolve()
        racine = PROJECT_ROOT.resolve()
        return str(absolu_resolu.relative_to(racine))
    except (OSError, ValueError):
        return str(absolu)


def _chemin_depuis_stockage(valeur: str) -> Path:
    chemin = Path(valeur)

    if chemin.is_absolute():
        return chemin

    return PROJECT_ROOT / chemin


def _decimal_texte(valeur: Decimal) -> str:
    return format(valeur, "f")


def _estimation_vers_dict(estimation: EstimationFiscale2025 | None):
    if estimation is None:
        return None
    r = estimation.rapprochement
    montant = r.remboursement_estime if r.remboursement_estime > 0 else r.solde_estime
    return {
        "resultat": r.resultat,
        "montant": _decimal_texte(montant),
        "impot_total_preliminaire": _decimal_texte(r.impot_total_preliminaire),
        "retenues_totales": _decimal_texte(r.retenues_totales),
    }



def _ajustement_reer_vers_dict(
    ajustement: AjustementReer2025 | None,
):
    if ajustement is None:
        ajustement = AjustementReer2025()

    valider_ajustement_reer_2025(ajustement)

    return {
        "deduction_reer": _decimal_texte(ajustement.deduction_reer),
        "plafond_reer_confirme": _decimal_texte(
            ajustement.plafond_reer_confirme
        ),
        "source_plafond_reer": ajustement.source_plafond_reer,
        "valide_par_comptable": bool(ajustement.valide_par_comptable),
        "inclut_transfert_reer": bool(ajustement.inclut_transfert_reer),
        "inclut_remboursement_rap_reep": bool(
            ajustement.inclut_remboursement_rap_reep
        ),
    }


def _ajustement_reer_depuis_dict(valeur: Any) -> AjustementReer2025:
    if valeur is None:
        return AjustementReer2025()

    if not isinstance(valeur, dict):
        raise ValueError("L'ajustement REER enregistré est invalide.")

    ajustement = AjustementReer2025(
        deduction_reer=_decimal_depuis_json(
            valeur.get("deduction_reer", "0"),
            "ajustement_reer.deduction_reer",
        ),
        plafond_reer_confirme=_decimal_depuis_json(
            valeur.get("plafond_reer_confirme", "0"),
            "ajustement_reer.plafond_reer_confirme",
        ),
        source_plafond_reer=str(valeur.get("source_plafond_reer", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        inclut_transfert_reer=bool(
            valeur.get("inclut_transfert_reer", False)
        ),
        inclut_remboursement_rap_reep=bool(
            valeur.get("inclut_remboursement_rap_reep", False)
        ),
    )
    return valider_ajustement_reer_2025(ajustement)


def _cotisations_syndicales_vers_dict(
    cotisations: CotisationsSyndicalesProfessionnelles2025 | None,
):
    if cotisations is None:
        cotisations = CotisationsSyndicalesProfessionnelles2025()

    valider_cotisations_syndicales_2025(cotisations)

    return {
        "montant_federal_admissible": _decimal_texte(
            cotisations.montant_federal_admissible
        ),
        "montant_quebec_admissible": _decimal_texte(
            cotisations.montant_quebec_admissible
        ),
        "source_federale": cotisations.source_federale,
        "source_quebec": cotisations.source_quebec,
        "valide_par_comptable": bool(
            cotisations.valide_par_comptable
        ),
        "sources_dedoublonnees": bool(
            cotisations.sources_dedoublonnees
        ),
    }


def _cotisations_syndicales_depuis_dict(
    valeur: Any,
) -> CotisationsSyndicalesProfessionnelles2025:
    if valeur is None:
        return CotisationsSyndicalesProfessionnelles2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les cotisations syndicales enregistrées sont invalides."
        )

    cotisations = CotisationsSyndicalesProfessionnelles2025(
        montant_federal_admissible=_decimal_depuis_json(
            valeur.get("montant_federal_admissible", "0"),
            "cotisations_syndicales.montant_federal_admissible",
        ),
        montant_quebec_admissible=_decimal_depuis_json(
            valeur.get("montant_quebec_admissible", "0"),
            "cotisations_syndicales.montant_quebec_admissible",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        sources_dedoublonnees=bool(
            valeur.get("sources_dedoublonnees", False)
        ),
    )
    return valider_cotisations_syndicales_2025(cotisations)



def _dons_bienfaisance_vers_dict(
    dons: DonsBienfaisance2025 | None,
):
    if dons is None:
        dons = DonsBienfaisance2025()

    valider_dons_bienfaisance_2025(dons)

    return {
        "montant_admissible_federal": _decimal_texte(
            dons.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            dons.montant_admissible_quebec
        ),
        "source_federale": dons.source_federale,
        "source_quebec": dons.source_quebec,
        "valide_par_comptable": bool(dons.valide_par_comptable),
        "donataire_reconnu_confirme": bool(
            dons.donataire_reconnu_confirme
        ),
        "dons_monetaires_2025_uniquement": bool(
            dons.dons_monetaires_2025_uniquement
        ),
        "aucun_report_anterieur": bool(
            dons.aucun_report_anterieur
        ),
        "inclut_dons_jan_fev_2025": bool(
            dons.inclut_dons_jan_fev_2025
        ),
        "dons_jan_fev_deja_reclames_2024": bool(
            dons.dons_jan_fev_deja_reclames_2024
        ),
    }


def _dons_bienfaisance_depuis_dict(
    valeur: Any,
) -> DonsBienfaisance2025:
    if valeur is None:
        return DonsBienfaisance2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les dons de bienfaisance enregistrés sont invalides."
        )

    dons = DonsBienfaisance2025(
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "dons_bienfaisance.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "dons_bienfaisance.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        donataire_reconnu_confirme=bool(
            valeur.get("donataire_reconnu_confirme", False)
        ),
        dons_monetaires_2025_uniquement=bool(
            valeur.get("dons_monetaires_2025_uniquement", False)
        ),
        aucun_report_anterieur=bool(
            valeur.get("aucun_report_anterieur", False)
        ),
        inclut_dons_jan_fev_2025=bool(
            valeur.get("inclut_dons_jan_fev_2025", False)
        ),
        dons_jan_fev_deja_reclames_2024=bool(
            valeur.get("dons_jan_fev_deja_reclames_2024", False)
        ),
    )
    return valider_dons_bienfaisance_2025(dons)


def _frais_medicaux_vers_dict(
    frais: FraisMedicaux2025 | None,
):
    if frais is None:
        frais = FraisMedicaux2025()

    valider_frais_medicaux_2025(frais)

    return {
        "montant_admissible_federal": _decimal_texte(
            frais.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            frais.montant_admissible_quebec
        ),
        "source_federale": frais.source_federale,
        "source_quebec": frais.source_quebec,
        "valide_par_comptable": bool(frais.valide_par_comptable),
        "recus_confirmes": bool(frais.recus_confirmes),
        "remboursements_soustraits": bool(
            frais.remboursements_soustraits
        ),
        "periode_12_mois_fin_2025_confirmee": bool(
            frais.periode_12_mois_fin_2025_confirmee
        ),
        "aucune_periode_deja_reclamee": bool(
            frais.aucune_periode_deja_reclamee
        ),
        "profil_individuel_sans_conjoint_dependant": bool(
            frais.profil_individuel_sans_conjoint_dependant
        ),
    }


def _frais_medicaux_depuis_dict(
    valeur: Any,
) -> FraisMedicaux2025:
    if valeur is None:
        return FraisMedicaux2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les frais médicaux enregistrés sont invalides."
        )

    frais = FraisMedicaux2025(
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "frais_medicaux.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "frais_medicaux.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        recus_confirmes=bool(
            valeur.get("recus_confirmes", False)
        ),
        remboursements_soustraits=bool(
            valeur.get("remboursements_soustraits", False)
        ),
        periode_12_mois_fin_2025_confirmee=bool(
            valeur.get(
                "periode_12_mois_fin_2025_confirmee",
                False,
            )
        ),
        aucune_periode_deja_reclamee=bool(
            valeur.get("aucune_periode_deja_reclamee", False)
        ),
        profil_individuel_sans_conjoint_dependant=bool(
            valeur.get(
                "profil_individuel_sans_conjoint_dependant",
                False,
            )
        ),
    )
    return valider_frais_medicaux_2025(frais)


def _frais_scolarite_vers_dict(
    frais: FraisScolarite2025 | None,
):
    if frais is None:
        frais = FraisScolarite2025()

    valider_frais_scolarite_2025(frais)

    return {
        "montant_admissible_federal": _decimal_texte(
            frais.montant_admissible_federal
        ),
        "montant_admissible_quebec": _decimal_texte(
            frais.montant_admissible_quebec
        ),
        "source_federale": frais.source_federale,
        "source_quebec": frais.source_quebec,
        "valide_par_comptable": bool(frais.valide_par_comptable),
        "piece_federale_confirmee": bool(frais.piece_federale_confirmee),
        "recu_officiel_quebec_confirme": bool(
            frais.recu_officiel_quebec_confirme
        ),
        "seuil_100_confirme": bool(frais.seuil_100_confirme),
        "remboursements_soustraits": bool(
            frais.remboursements_soustraits
        ),
        "frais_2025_uniquement": bool(frais.frais_2025_uniquement),
        "aucun_report_anterieur": bool(frais.aucun_report_anterieur),
        "aucun_transfert": bool(frais.aucun_transfert),
        "credit_canadien_formation_non_reclame": bool(
            frais.credit_canadien_formation_non_reclame
        ),
        "profil_resident_quebec_simple": bool(
            frais.profil_resident_quebec_simple
        ),
    }


def _frais_scolarite_depuis_dict(
    valeur: Any,
) -> FraisScolarite2025:
    if valeur is None:
        return FraisScolarite2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les frais de scolarité enregistrés sont invalides."
        )

    frais = FraisScolarite2025(
        montant_admissible_federal=_decimal_depuis_json(
            valeur.get("montant_admissible_federal", "0"),
            "frais_scolarite.montant_admissible_federal",
        ),
        montant_admissible_quebec=_decimal_depuis_json(
            valeur.get("montant_admissible_quebec", "0"),
            "frais_scolarite.montant_admissible_quebec",
        ),
        source_federale=str(valeur.get("source_federale", "")),
        source_quebec=str(valeur.get("source_quebec", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        piece_federale_confirmee=bool(
            valeur.get("piece_federale_confirmee", False)
        ),
        recu_officiel_quebec_confirme=bool(
            valeur.get("recu_officiel_quebec_confirme", False)
        ),
        seuil_100_confirme=bool(
            valeur.get("seuil_100_confirme", False)
        ),
        remboursements_soustraits=bool(
            valeur.get("remboursements_soustraits", False)
        ),
        frais_2025_uniquement=bool(
            valeur.get("frais_2025_uniquement", False)
        ),
        aucun_report_anterieur=bool(
            valeur.get("aucun_report_anterieur", False)
        ),
        aucun_transfert=bool(
            valeur.get("aucun_transfert", False)
        ),
        credit_canadien_formation_non_reclame=bool(
            valeur.get("credit_canadien_formation_non_reclame", False)
        ),
        profil_resident_quebec_simple=bool(
            valeur.get("profil_resident_quebec_simple", False)
        ),
    )
    return valider_frais_scolarite_2025(frais)


def _credit_deficience_vers_dict(
    credit: CreditDeficience2025 | None,
):
    if credit is None:
        credit = CreditDeficience2025()

    valider_credit_deficience_2025(credit)

    return {
        "reclamer_federal": bool(credit.reclamer_federal),
        "reclamer_quebec": bool(credit.reclamer_quebec),
        "source_federale": credit.source_federale,
        "source_quebec": credit.source_quebec,
        "valide_par_comptable": bool(credit.valide_par_comptable),
        "age_18_plus_au_1_janvier_2025": bool(
            credit.age_18_plus_au_1_janvier_2025
        ),
        "deficience_12_mois_confirmee": bool(
            credit.deficience_12_mois_confirmee
        ),
        "profil_soi_meme_resident_quebec": bool(
            credit.profil_soi_meme_resident_quebec
        ),
        "ciph_approuve_arc": bool(credit.ciph_approuve_arc),
        "attestation_quebec_confirmee": bool(
            credit.attestation_quebec_confirmee
        ),
        "aucun_conflit_soins_prepose_etablissement": bool(
            credit.aucun_conflit_soins_prepose_etablissement
        ),
        "aucun_transfert_federal": bool(
            credit.aucun_transfert_federal
        ),
    }


def _credit_deficience_depuis_dict(
    valeur: Any,
) -> CreditDeficience2025:
    if valeur is None:
        return CreditDeficience2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le crédit handicap/déficience enregistré est invalide."
        )

    credit = CreditDeficience2025(
        reclamer_federal=bool(
            valeur.get("reclamer_federal", False)
        ),
        reclamer_quebec=bool(
            valeur.get("reclamer_quebec", False)
        ),
        source_federale=str(
            valeur.get("source_federale", "")
        ),
        source_quebec=str(
            valeur.get("source_quebec", "")
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        age_18_plus_au_1_janvier_2025=bool(
            valeur.get("age_18_plus_au_1_janvier_2025", False)
        ),
        deficience_12_mois_confirmee=bool(
            valeur.get("deficience_12_mois_confirmee", False)
        ),
        profil_soi_meme_resident_quebec=bool(
            valeur.get("profil_soi_meme_resident_quebec", False)
        ),
        ciph_approuve_arc=bool(
            valeur.get("ciph_approuve_arc", False)
        ),
        attestation_quebec_confirmee=bool(
            valeur.get("attestation_quebec_confirmee", False)
        ),
        aucun_conflit_soins_prepose_etablissement=bool(
            valeur.get(
                "aucun_conflit_soins_prepose_etablissement",
                False,
            )
        ),
        aucun_transfert_federal=bool(
            valeur.get("aucun_transfert_federal", False)
        ),
    )
    return valider_credit_deficience_2025(credit)


def _assurance_medicaments_vers_dict(
    assurance: AssuranceMedicamentsQuebec2025 | None,
):
    if assurance is None:
        assurance = AssuranceMedicamentsQuebec2025()

    valider_assurance_medicaments_2025(assurance)

    return {
        "type_couverture": assurance.type_couverture,
        "couverture_toute_annee": bool(
            assurance.couverture_toute_annee
        ),
        "sans_conjoint_31_decembre_2025": bool(
            assurance.sans_conjoint_31_decembre_2025
        ),
        "revenu_ligne_275": _decimal_texte(
            assurance.revenu_ligne_275
        ),
        "revenu_ligne_48_annexe_k": _decimal_texte(
            assurance.revenu_ligne_48_annexe_k
        ),
        "aucun_mois_exempt": bool(assurance.aucun_mois_exempt),
        "carte_ramq_valide_2025": bool(
            assurance.carte_ramq_valide_2025
        ),
        "situation_validee_par_comptable": bool(
            assurance.situation_validee_par_comptable
        ),
        "aucun_cas_particulier": bool(
            assurance.aucun_cas_particulier
        ),
        "source": assurance.source,
        "code_case_449": assurance.code_case_449,
    }


def _assurance_medicaments_depuis_dict(
    valeur: Any,
) -> AssuranceMedicamentsQuebec2025:
    if valeur is None:
        return AssuranceMedicamentsQuebec2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "L'assurance médicaments enregistrée est invalide."
        )

    assurance = AssuranceMedicamentsQuebec2025(
        type_couverture=str(
            valeur.get("type_couverture", "")
        ),
        couverture_toute_annee=bool(
            valeur.get("couverture_toute_annee", False)
        ),
        sans_conjoint_31_decembre_2025=bool(
            valeur.get(
                "sans_conjoint_31_decembre_2025",
                False,
            )
        ),
        revenu_ligne_275=_decimal_depuis_json(
            valeur.get("revenu_ligne_275", "0"),
            "assurance_medicaments.revenu_ligne_275",
        ),
        revenu_ligne_48_annexe_k=_decimal_depuis_json(
            valeur.get("revenu_ligne_48_annexe_k", "0"),
            "assurance_medicaments.revenu_ligne_48_annexe_k",
        ),
        aucun_mois_exempt=bool(
            valeur.get("aucun_mois_exempt", False)
        ),
        carte_ramq_valide_2025=bool(
            valeur.get("carte_ramq_valide_2025", False)
        ),
        situation_validee_par_comptable=bool(
            valeur.get(
                "situation_validee_par_comptable",
                False,
            )
        ),
        aucun_cas_particulier=bool(
            valeur.get("aucun_cas_particulier", False)
        ),
        source=str(valeur.get("source", "")),
        code_case_449=str(
            valeur.get("code_case_449", "")
        ),
    )
    return valider_assurance_medicaments_2025(assurance)


def _cotisations_excedentaires_vers_dict(
    cotisations: CotisationsExcedentaires2025 | None,
):
    if cotisations is None:
        cotisations = CotisationsExcedentaires2025()

    valider_cotisations_excedentaires_2025(cotisations)

    return {
        "rrq_ba": _decimal_texte(cotisations.rrq_ba),
        "rrq_bb": _decimal_texte(cotisations.rrq_bb),
        "gains_admissibles_rrq": _decimal_texte(
            cotisations.gains_admissibles_rrq
        ),
        "assurance_emploi": _decimal_texte(
            cotisations.assurance_emploi
        ),
        "gains_assurables_ae": _decimal_texte(
            cotisations.gains_assurables_ae
        ),
        "rqap": _decimal_texte(cotisations.rqap),
        "revenus_assujettis_rqap": _decimal_texte(
            cotisations.revenus_assujettis_rqap
        ),
        "source": cotisations.source,
        "valide_par_comptable": bool(
            cotisations.valide_par_comptable
        ),
        "resident_quebec_31_decembre_2025": bool(
            cotisations.resident_quebec_31_decembre_2025
        ),
        "emploi_quebec_uniquement": bool(
            cotisations.emploi_quebec_uniquement
        ),
        "rrq_uniquement_sans_rpc": bool(
            cotisations.rrq_uniquement_sans_rpc
        ),
        "aucun_travail_autonome": bool(
            cotisations.aucun_travail_autonome
        ),
        "profil_rrq_standard_18_64": bool(
            cotisations.profil_rrq_standard_18_64
        ),
        "aucun_cas_particulier_ae": bool(
            cotisations.aucun_cas_particulier_ae
        ),
        "aucun_cas_particulier_rqap": bool(
            cotisations.aucun_cas_particulier_rqap
        ),
        "calcul_standard_confirme": bool(
            cotisations.calcul_standard_confirme
        ),
    }


def _cotisations_excedentaires_depuis_dict(
    valeur: Any,
) -> CotisationsExcedentaires2025:
    if valeur is None:
        return CotisationsExcedentaires2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Les cotisations excédentaires enregistrées sont invalides."
        )

    cotisations = CotisationsExcedentaires2025(
        rrq_ba=_decimal_depuis_json(
            valeur.get("rrq_ba", "0"),
            "cotisations_excedentaires.rrq_ba",
        ),
        rrq_bb=_decimal_depuis_json(
            valeur.get("rrq_bb", "0"),
            "cotisations_excedentaires.rrq_bb",
        ),
        gains_admissibles_rrq=_decimal_depuis_json(
            valeur.get("gains_admissibles_rrq", "0"),
            "cotisations_excedentaires.gains_admissibles_rrq",
        ),
        assurance_emploi=_decimal_depuis_json(
            valeur.get("assurance_emploi", "0"),
            "cotisations_excedentaires.assurance_emploi",
        ),
        gains_assurables_ae=_decimal_depuis_json(
            valeur.get("gains_assurables_ae", "0"),
            "cotisations_excedentaires.gains_assurables_ae",
        ),
        rqap=_decimal_depuis_json(
            valeur.get("rqap", "0"),
            "cotisations_excedentaires.rqap",
        ),
        revenus_assujettis_rqap=_decimal_depuis_json(
            valeur.get("revenus_assujettis_rqap", "0"),
            "cotisations_excedentaires.revenus_assujettis_rqap",
        ),
        source=str(valeur.get("source", "")),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        resident_quebec_31_decembre_2025=bool(
            valeur.get(
                "resident_quebec_31_decembre_2025",
                False,
            )
        ),
        emploi_quebec_uniquement=bool(
            valeur.get("emploi_quebec_uniquement", False)
        ),
        rrq_uniquement_sans_rpc=bool(
            valeur.get("rrq_uniquement_sans_rpc", False)
        ),
        aucun_travail_autonome=bool(
            valeur.get("aucun_travail_autonome", False)
        ),
        profil_rrq_standard_18_64=bool(
            valeur.get("profil_rrq_standard_18_64", False)
        ),
        aucun_cas_particulier_ae=bool(
            valeur.get("aucun_cas_particulier_ae", False)
        ),
        aucun_cas_particulier_rqap=bool(
            valeur.get("aucun_cas_particulier_rqap", False)
        ),
        calcul_standard_confirme=bool(
            valeur.get("calcul_standard_confirme", False)
        ),
    )
    return valider_cotisations_excedentaires_2025(cotisations)


def _personne_vivant_seule_vers_dict(
    profil: PersonneVivantSeule2025 | None,
):
    if profil is None:
        profil = PersonneVivantSeule2025()

    valider_personne_vivant_seule_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_familial_net": _decimal_texte(
            profil.revenu_familial_net
        ),
        "personne_vivant_seule_toute_annee": bool(
            profil.personne_vivant_seule_toute_annee
        ),
        "habitation_maintenue_par_contribuable": bool(
            profil.habitation_maintenue_par_contribuable
        ),
        "seulement_personnes_autorisees_dans_habitation": bool(
            profil.seulement_personnes_autorisees_dans_habitation
        ),
        "aucun_conjoint_31_decembre_2025": bool(
            profil.aucun_conjoint_31_decembre_2025
        ),
        "resident_quebec_canada_toute_annee": bool(
            profil.resident_quebec_canada_toute_annee
        ),
        "reclamer_additionnel_monoparental": bool(
            profil.reclamer_additionnel_monoparental
        ),
        "enfant_majeur_etudes_admissible": bool(
            profil.enfant_majeur_etudes_admissible
        ),
        "aucun_droit_allocation_famille_decembre": bool(
            profil.aucun_droit_allocation_famille_decembre
        ),
        "mois_allocation_famille_2025": int(
            profil.mois_allocation_famille_2025
        ),
        "aucun_montant_age_ou_retraite": bool(
            profil.aucun_montant_age_ou_retraite
        ),
        "documents_justificatifs_confirmes": bool(
            profil.documents_justificatifs_confirmes
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source": profil.source,
    }


def _personne_vivant_seule_depuis_dict(
    valeur: Any,
) -> PersonneVivantSeule2025:
    if valeur is None:
        return PersonneVivantSeule2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil personne vivant seule enregistré est invalide."
        )

    try:
        mois_allocation = int(
            valeur.get("mois_allocation_famille_2025", 0)
        )
    except (TypeError, ValueError) as erreur:
        raise ValueError(
            "Le nombre de mois d'Allocation famille enregistré "
            "est invalide."
        ) from erreur

    profil = PersonneVivantSeule2025(
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_familial_net=_decimal_depuis_json(
            valeur.get("revenu_familial_net", "0"),
            "personne_vivant_seule.revenu_familial_net",
        ),
        personne_vivant_seule_toute_annee=bool(
            valeur.get(
                "personne_vivant_seule_toute_annee",
                False,
            )
        ),
        habitation_maintenue_par_contribuable=bool(
            valeur.get(
                "habitation_maintenue_par_contribuable",
                False,
            )
        ),
        seulement_personnes_autorisees_dans_habitation=bool(
            valeur.get(
                "seulement_personnes_autorisees_dans_habitation",
                False,
            )
        ),
        aucun_conjoint_31_decembre_2025=bool(
            valeur.get(
                "aucun_conjoint_31_decembre_2025",
                False,
            )
        ),
        resident_quebec_canada_toute_annee=bool(
            valeur.get(
                "resident_quebec_canada_toute_annee",
                False,
            )
        ),
        reclamer_additionnel_monoparental=bool(
            valeur.get(
                "reclamer_additionnel_monoparental",
                False,
            )
        ),
        enfant_majeur_etudes_admissible=bool(
            valeur.get(
                "enfant_majeur_etudes_admissible",
                False,
            )
        ),
        aucun_droit_allocation_famille_decembre=bool(
            valeur.get(
                "aucun_droit_allocation_famille_decembre",
                False,
            )
        ),
        mois_allocation_famille_2025=mois_allocation,
        aucun_montant_age_ou_retraite=bool(
            valeur.get(
                "aucun_montant_age_ou_retraite",
                False,
            )
        ),
        documents_justificatifs_confirmes=bool(
            valeur.get(
                "documents_justificatifs_confirmes",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source=str(valeur.get("source", "")),
    )
    return valider_personne_vivant_seule_2025(profil)


def _credits_federaux_age_pension_vers_dict(
    profil: CreditsFederauxAgePension2025 | None,
):
    if profil is None:
        profil = CreditsFederauxAgePension2025()

    valider_credits_federaux_age_pension_2025(profil)

    return {
        "reclamer_montant_age": bool(
            profil.reclamer_montant_age
        ),
        "age_65_plus_31_decembre_2025": bool(
            profil.age_65_plus_31_decembre_2025
        ),
        "revenu_net_ligne_23600": _decimal_texte(
            profil.revenu_net_ligne_23600
        ),
        "reclamer_montant_pension": bool(
            profil.reclamer_montant_pension
        ),
        "revenu_pension_admissible": _decimal_texte(
            profil.revenu_pension_admissible
        ),
        "resident_canada_toute_annee": bool(
            profil.resident_canada_toute_annee
        ),
        "aucune_regle_deces": bool(
            profil.aucune_regle_deces
        ),
        "aucun_fractionnement_pension": bool(
            profil.aucun_fractionnement_pension
        ),
        "aucun_transfert_conjoint": bool(
            profil.aucun_transfert_conjoint
        ),
        "revenu_pension_admissible_confirme": bool(
            profil.revenu_pension_admissible_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_age": profil.source_age,
        "source_pension": profil.source_pension,
    }


def _credits_federaux_age_pension_depuis_dict(
    valeur: Any,
) -> CreditsFederauxAgePension2025:
    if valeur is None:
        return CreditsFederauxAgePension2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil âge/pension fédéral enregistré est invalide."
        )

    profil = CreditsFederauxAgePension2025(
        reclamer_montant_age=bool(
            valeur.get("reclamer_montant_age", False)
        ),
        age_65_plus_31_decembre_2025=bool(
            valeur.get(
                "age_65_plus_31_decembre_2025",
                False,
            )
        ),
        revenu_net_ligne_23600=_decimal_depuis_json(
            valeur.get("revenu_net_ligne_23600", "0"),
            (
                "credits_federaux_age_pension."
                "revenu_net_ligne_23600"
            ),
        ),
        reclamer_montant_pension=bool(
            valeur.get("reclamer_montant_pension", False)
        ),
        revenu_pension_admissible=_decimal_depuis_json(
            valeur.get("revenu_pension_admissible", "0"),
            (
                "credits_federaux_age_pension."
                "revenu_pension_admissible"
            ),
        ),
        resident_canada_toute_annee=bool(
            valeur.get(
                "resident_canada_toute_annee",
                False,
            )
        ),
        aucune_regle_deces=bool(
            valeur.get("aucune_regle_deces", False)
        ),
        aucun_fractionnement_pension=bool(
            valeur.get(
                "aucun_fractionnement_pension",
                False,
            )
        ),
        aucun_transfert_conjoint=bool(
            valeur.get("aucun_transfert_conjoint", False)
        ),
        revenu_pension_admissible_confirme=bool(
            valeur.get(
                "revenu_pension_admissible_confirme",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_age=str(
            valeur.get("source_age", "")
        ),
        source_pension=str(
            valeur.get("source_pension", "")
        ),
    )
    return valider_credits_federaux_age_pension_2025(profil)


def _montant_conjoint_federal_vers_dict(
    profil: MontantConjointFederal2025 | None,
):
    if profil is None:
        profil = MontantConjointFederal2025()

    valider_montant_conjoint_federal_2025(profil)

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_net_contribuable_ligne_23600": _decimal_texte(
            profil.revenu_net_contribuable_ligne_23600
        ),
        "revenu_net_conjoint_2025": _decimal_texte(
            profil.revenu_net_conjoint_2025
        ),
        "contribuable_resident_canada_toute_annee": bool(
            profil.contribuable_resident_canada_toute_annee
        ),
        "relation_conjoint_confirmee": bool(
            profil.relation_conjoint_confirmee
        ),
        "conjoint_soutenu_2025": bool(
            profil.conjoint_soutenu_2025
        ),
        "meme_conjoint_toute_annee_2025": bool(
            profil.meme_conjoint_toute_annee_2025
        ),
        "aucune_separation_2025": bool(
            profil.aucune_separation_2025
        ),
        "conjoint_resident_canada_toute_annee": bool(
            profil.conjoint_resident_canada_toute_annee
        ),
        "aucun_paiement_pension_alimentaire": bool(
            profil.aucun_paiement_pension_alimentaire
        ),
        "aucune_infirmite_conjoint": bool(
            profil.aucune_infirmite_conjoint
        ),
        "un_seul_conjoint_reclame_montant": bool(
            profil.un_seul_conjoint_reclame_montant
        ),
        "revenu_conjoint_confirme": bool(
            profil.revenu_conjoint_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_conjoint": profil.source_conjoint,
    }


def _montant_conjoint_federal_depuis_dict(
    valeur: Any,
) -> MontantConjointFederal2025:
    if valeur is None:
        return MontantConjointFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour conjoint enregistré est invalide."
        )

    profil = MontantConjointFederal2025(
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_net_contribuable_ligne_23600=_decimal_depuis_json(
            valeur.get(
                "revenu_net_contribuable_ligne_23600",
                "0",
            ),
            (
                "montant_conjoint_federal."
                "revenu_net_contribuable_ligne_23600"
            ),
        ),
        revenu_net_conjoint_2025=_decimal_depuis_json(
            valeur.get("revenu_net_conjoint_2025", "0"),
            "montant_conjoint_federal.revenu_net_conjoint_2025",
        ),
        contribuable_resident_canada_toute_annee=bool(
            valeur.get(
                "contribuable_resident_canada_toute_annee",
                False,
            )
        ),
        relation_conjoint_confirmee=bool(
            valeur.get("relation_conjoint_confirmee", False)
        ),
        conjoint_soutenu_2025=bool(
            valeur.get("conjoint_soutenu_2025", False)
        ),
        meme_conjoint_toute_annee_2025=bool(
            valeur.get("meme_conjoint_toute_annee_2025", False)
        ),
        aucune_separation_2025=bool(
            valeur.get("aucune_separation_2025", False)
        ),
        conjoint_resident_canada_toute_annee=bool(
            valeur.get(
                "conjoint_resident_canada_toute_annee",
                False,
            )
        ),
        aucun_paiement_pension_alimentaire=bool(
            valeur.get(
                "aucun_paiement_pension_alimentaire",
                False,
            )
        ),
        aucune_infirmite_conjoint=bool(
            valeur.get("aucune_infirmite_conjoint", False)
        ),
        un_seul_conjoint_reclame_montant=bool(
            valeur.get(
                "un_seul_conjoint_reclame_montant",
                False,
            )
        ),
        revenu_conjoint_confirme=bool(
            valeur.get("revenu_conjoint_confirme", False)
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_conjoint=str(
            valeur.get("source_conjoint", "")
        ),
    )

    return valider_montant_conjoint_federal_2025(profil)



def _personne_charge_admissible_federale_vers_dict(
    profil: MontantPersonneChargeAdmissibleFederal2025 | None,
):
    if profil is None:
        profil = MontantPersonneChargeAdmissibleFederal2025()

    valider_montant_personne_charge_admissible_federal_2025(
        profil
    )

    return {
        "reclamer_montant": bool(profil.reclamer_montant),
        "revenu_net_contribuable_ligne_23600": _decimal_texte(
            profil.revenu_net_contribuable_ligne_23600
        ),
        "revenu_net_personne_charge_2025": _decimal_texte(
            profil.revenu_net_personne_charge_2025
        ),
        "contribuable_resident_canada_toute_annee": bool(
            profil.contribuable_resident_canada_toute_annee
        ),
        "aucun_epoux_conjoint_2025": bool(
            profil.aucun_epoux_conjoint_2025
        ),
        "personne_charge_est_enfant": bool(
            profil.personne_charge_est_enfant
        ),
        "enfant_moins_18_fin_2025": bool(
            profil.enfant_moins_18_fin_2025
        ),
        "aucune_infirmite_enfant": bool(
            profil.aucune_infirmite_enfant
        ),
        "enfant_soutenu_2025": bool(
            profil.enfant_soutenu_2025
        ),
        "enfant_a_vecu_avec_contribuable": bool(
            profil.enfant_a_vecu_avec_contribuable
        ),
        "habitation_maintenue_par_contribuable": bool(
            profil.habitation_maintenue_par_contribuable
        ),
        "enfant_resident_canada_toute_annee": bool(
            profil.enfant_resident_canada_toute_annee
        ),
        "aucune_garde_partagee": bool(
            profil.aucune_garde_partagee
        ),
        "aucun_paiement_pension_alimentaire": bool(
            profil.aucun_paiement_pension_alimentaire
        ),
        "un_seul_montant_30400_par_menage": bool(
            profil.un_seul_montant_30400_par_menage
        ),
        "aucun_autre_reclamant_30400": bool(
            profil.aucun_autre_reclamant_30400
        ),
        "revenu_personne_charge_confirme": bool(
            profil.revenu_personne_charge_confirme
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_personne_charge": profil.source_personne_charge,
    }


def _personne_charge_admissible_federale_depuis_dict(
    valeur: Any,
) -> MontantPersonneChargeAdmissibleFederal2025:
    if valeur is None:
        return MontantPersonneChargeAdmissibleFederal2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le montant fédéral pour personne à charge "
            "admissible enregistré est invalide."
        )

    profil = MontantPersonneChargeAdmissibleFederal2025(
        reclamer_montant=bool(
            valeur.get("reclamer_montant", False)
        ),
        revenu_net_contribuable_ligne_23600=_decimal_depuis_json(
            valeur.get(
                "revenu_net_contribuable_ligne_23600",
                "0",
            ),
            (
                "personne_charge_admissible_federale."
                "revenu_net_contribuable_ligne_23600"
            ),
        ),
        revenu_net_personne_charge_2025=_decimal_depuis_json(
            valeur.get(
                "revenu_net_personne_charge_2025",
                "0",
            ),
            (
                "personne_charge_admissible_federale."
                "revenu_net_personne_charge_2025"
            ),
        ),
        contribuable_resident_canada_toute_annee=bool(
            valeur.get(
                "contribuable_resident_canada_toute_annee",
                False,
            )
        ),
        aucun_epoux_conjoint_2025=bool(
            valeur.get("aucun_epoux_conjoint_2025", False)
        ),
        personne_charge_est_enfant=bool(
            valeur.get("personne_charge_est_enfant", False)
        ),
        enfant_moins_18_fin_2025=bool(
            valeur.get("enfant_moins_18_fin_2025", False)
        ),
        aucune_infirmite_enfant=bool(
            valeur.get("aucune_infirmite_enfant", False)
        ),
        enfant_soutenu_2025=bool(
            valeur.get("enfant_soutenu_2025", False)
        ),
        enfant_a_vecu_avec_contribuable=bool(
            valeur.get(
                "enfant_a_vecu_avec_contribuable",
                False,
            )
        ),
        habitation_maintenue_par_contribuable=bool(
            valeur.get(
                "habitation_maintenue_par_contribuable",
                False,
            )
        ),
        enfant_resident_canada_toute_annee=bool(
            valeur.get(
                "enfant_resident_canada_toute_annee",
                False,
            )
        ),
        aucune_garde_partagee=bool(
            valeur.get("aucune_garde_partagee", False)
        ),
        aucun_paiement_pension_alimentaire=bool(
            valeur.get(
                "aucun_paiement_pension_alimentaire",
                False,
            )
        ),
        un_seul_montant_30400_par_menage=bool(
            valeur.get(
                "un_seul_montant_30400_par_menage",
                False,
            )
        ),
        aucun_autre_reclamant_30400=bool(
            valeur.get(
                "aucun_autre_reclamant_30400",
                False,
            )
        ),
        revenu_personne_charge_confirme=bool(
            valeur.get(
                "revenu_personne_charge_confirme",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_personne_charge=str(
            valeur.get("source_personne_charge", "")
        ),
    )

    return valider_montant_personne_charge_admissible_federal_2025(
        profil
    )

def _montants_age_retraite_vers_dict(
    profil: MontantsAgeRetraite2025 | None,
):
    if profil is None:
        profil = MontantsAgeRetraite2025()

    valider_montants_age_retraite_2025(profil)

    return {
        "reclamer_age": bool(profil.reclamer_age),
        "ne_avant_1_janvier_1961": bool(
            profil.ne_avant_1_janvier_1961
        ),
        "reclamer_revenus_retraite": bool(
            profil.reclamer_revenus_retraite
        ),
        "revenu_ligne_122": _decimal_texte(
            profil.revenu_ligne_122
        ),
        "revenu_ligne_123": _decimal_texte(
            profil.revenu_ligne_123
        ),
        "deduction_ligne_250_point_4": _decimal_texte(
            profil.deduction_ligne_250_point_4
        ),
        "deduction_ligne_250_point_6": _decimal_texte(
            profil.deduction_ligne_250_point_6
        ),
        "deduction_ligne_293": _decimal_texte(
            profil.deduction_ligne_293
        ),
        "deduction_ligne_297_points_9_12": _decimal_texte(
            profil.deduction_ligne_297_points_9_12
        ),
        "transfert_revenus_retraite_ligne_245": _decimal_texte(
            profil.transfert_revenus_retraite_ligne_245
        ),
        "revenu_familial_net": _decimal_texte(
            profil.revenu_familial_net
        ),
        "aucun_conjoint_31_decembre_2025": bool(
            profil.aucun_conjoint_31_decembre_2025
        ),
        "resident_quebec_canada_toute_annee": bool(
            profil.resident_quebec_canada_toute_annee
        ),
        "aucun_montant_personne_vivant_seule": bool(
            profil.aucun_montant_personne_vivant_seule
        ),
        "revenus_retraite_admissibles_confirmes": bool(
            profil.revenus_retraite_admissibles_confirmes
        ),
        "revenus_non_admissibles_exclus": bool(
            profil.revenus_non_admissibles_exclus
        ),
        "valide_par_comptable": bool(
            profil.valide_par_comptable
        ),
        "source_age": profil.source_age,
        "source_retraite": profil.source_retraite,
    }


def _montants_age_retraite_depuis_dict(
    valeur: Any,
) -> MontantsAgeRetraite2025:
    if valeur is None:
        return MontantsAgeRetraite2025()

    if not isinstance(valeur, dict):
        raise ValueError(
            "Le profil âge/retraite enregistré est invalide."
        )

    profil = MontantsAgeRetraite2025(
        reclamer_age=bool(
            valeur.get("reclamer_age", False)
        ),
        ne_avant_1_janvier_1961=bool(
            valeur.get("ne_avant_1_janvier_1961", False)
        ),
        reclamer_revenus_retraite=bool(
            valeur.get("reclamer_revenus_retraite", False)
        ),
        revenu_ligne_122=_decimal_depuis_json(
            valeur.get("revenu_ligne_122", "0"),
            "montants_age_retraite.revenu_ligne_122",
        ),
        revenu_ligne_123=_decimal_depuis_json(
            valeur.get("revenu_ligne_123", "0"),
            "montants_age_retraite.revenu_ligne_123",
        ),
        deduction_ligne_250_point_4=_decimal_depuis_json(
            valeur.get("deduction_ligne_250_point_4", "0"),
            "montants_age_retraite.deduction_ligne_250_point_4",
        ),
        deduction_ligne_250_point_6=_decimal_depuis_json(
            valeur.get("deduction_ligne_250_point_6", "0"),
            "montants_age_retraite.deduction_ligne_250_point_6",
        ),
        deduction_ligne_293=_decimal_depuis_json(
            valeur.get("deduction_ligne_293", "0"),
            "montants_age_retraite.deduction_ligne_293",
        ),
        deduction_ligne_297_points_9_12=_decimal_depuis_json(
            valeur.get("deduction_ligne_297_points_9_12", "0"),
            "montants_age_retraite.deduction_ligne_297_points_9_12",
        ),
        transfert_revenus_retraite_ligne_245=_decimal_depuis_json(
            valeur.get(
                "transfert_revenus_retraite_ligne_245",
                "0",
            ),
            (
                "montants_age_retraite."
                "transfert_revenus_retraite_ligne_245"
            ),
        ),
        revenu_familial_net=_decimal_depuis_json(
            valeur.get("revenu_familial_net", "0"),
            "montants_age_retraite.revenu_familial_net",
        ),
        aucun_conjoint_31_decembre_2025=bool(
            valeur.get(
                "aucun_conjoint_31_decembre_2025",
                False,
            )
        ),
        resident_quebec_canada_toute_annee=bool(
            valeur.get(
                "resident_quebec_canada_toute_annee",
                False,
            )
        ),
        aucun_montant_personne_vivant_seule=bool(
            valeur.get(
                "aucun_montant_personne_vivant_seule",
                False,
            )
        ),
        revenus_retraite_admissibles_confirmes=bool(
            valeur.get(
                "revenus_retraite_admissibles_confirmes",
                False,
            )
        ),
        revenus_non_admissibles_exclus=bool(
            valeur.get(
                "revenus_non_admissibles_exclus",
                False,
            )
        ),
        valide_par_comptable=bool(
            valeur.get("valide_par_comptable", False)
        ),
        source_age=str(
            valeur.get("source_age", "")
        ),
        source_retraite=str(
            valeur.get("source_retraite", "")
        ),
    )
    return valider_montants_age_retraite_2025(profil)


def sauvegarder_dossier_fiscal(
    dossier: DossierFiscalValide,
    *,
    estimation: EstimationFiscale2025 | None = None,
    ajustement_reer: AjustementReer2025 | None = None,
    cotisations_syndicales: (
        CotisationsSyndicalesProfessionnelles2025 | None
    ) = None,
    dons_bienfaisance: DonsBienfaisance2025 | None = None,
    frais_medicaux: FraisMedicaux2025 | None = None,
    frais_scolarite: FraisScolarite2025 | None = None,
    credit_deficience: CreditDeficience2025 | None = None,
    assurance_medicaments: AssuranceMedicamentsQuebec2025 | None = None,
    cotisations_excedentaires: CotisationsExcedentaires2025 | None = None,
    personne_vivant_seule: PersonneVivantSeule2025 | None = None,
    montants_age_retraite: MontantsAgeRetraite2025 | None = None,
    credits_federaux_age_pension: CreditsFederauxAgePension2025 | None = None,
    montant_conjoint_federal: MontantConjointFederal2025 | None = None,
    personne_charge_admissible_federale: (
        MontantPersonneChargeAdmissibleFederal2025 | None
    ) = None,
    rapport_pdf: Path | str | None = None,
    destination: Path | str | None = None,
) -> Path:
    if destination is None:
        DOSSIERS_FISCAUX_DIR.mkdir(parents=True, exist_ok=True)
        chemin = DOSSIERS_FISCAUX_DIR / nom_fichier_dossier_fiscal(dossier)
    else:
        chemin = Path(destination)
        if chemin.suffix.lower() != ".json":
            chemin = chemin.with_suffix(".json")
        chemin.parent.mkdir(parents=True, exist_ok=True)

    contenu = {
        "schema_version": SCHEMA_VERSION,
        "sauvegarde_le": datetime.now().astimezone().isoformat(timespec="seconds"),
        "client": dossier.client,
        "annee_fiscale": dossier.annee_fiscale,
        "province": dossier.province,
        "documents": [_chemin_vers_stockage(x) for x in dossier.documents],
        "donnees_validees": [
            {
                "document": _chemin_vers_stockage(d.document),
                "type_document": d.type_document,
                "case": d.case,
                "libelle": d.libelle,
                "valeur_extraite": _decimal_texte(d.valeur_extraite),
                "valeur_validee": _decimal_texte(d.valeur_validee),
                "corrigee": bool(d.corrigee),
                "statut": d.statut,
            }
            for d in dossier.donnees_validees
        ],
        "derniere_estimation": _estimation_vers_dict(estimation),
        "ajustement_reer": _ajustement_reer_vers_dict(
            ajustement_reer
        ),
        "cotisations_syndicales": _cotisations_syndicales_vers_dict(
            cotisations_syndicales
        ),
        "dons_bienfaisance": _dons_bienfaisance_vers_dict(
            dons_bienfaisance
        ),
        "frais_medicaux": _frais_medicaux_vers_dict(
            frais_medicaux
        ),
        "frais_scolarite": _frais_scolarite_vers_dict(
            frais_scolarite
        ),
        "credit_deficience": _credit_deficience_vers_dict(
            credit_deficience
        ),
        "assurance_medicaments": _assurance_medicaments_vers_dict(
            assurance_medicaments
        ),
        "cotisations_excedentaires": _cotisations_excedentaires_vers_dict(
            cotisations_excedentaires
        ),
        "personne_vivant_seule": _personne_vivant_seule_vers_dict(
            personne_vivant_seule
        ),
        "montants_age_retraite": _montants_age_retraite_vers_dict(
            montants_age_retraite
        ),
        "credits_federaux_age_pension": _credits_federaux_age_pension_vers_dict(
            credits_federaux_age_pension
        ),
        "montant_conjoint_federal": _montant_conjoint_federal_vers_dict(
            montant_conjoint_federal
        ),
        "personne_charge_admissible_federale": (
            _personne_charge_admissible_federale_vers_dict(
                personne_charge_admissible_federale
            )
        ),
        "rapport_pdf": _chemin_vers_stockage(Path(rapport_pdf)) if rapport_pdf else None,
    }

    temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
    try:
        temporaire.write_text(json.dumps(contenu, ensure_ascii=False, indent=2), encoding="utf-8")
        temporaire.replace(chemin)
    finally:
        try:
            temporaire.unlink()
        except OSError:
            pass
    return chemin


def _decimal_depuis_json(valeur: Any, nom: str) -> Decimal:
    try:
        resultat = Decimal(str(valeur))
    except (InvalidOperation, ValueError, TypeError) as erreur:
        raise ValueError(f"Valeur décimale invalide pour {nom}.") from erreur
    if not resultat.is_finite():
        raise ValueError(f"Valeur décimale non finie pour {nom}.")
    return resultat


def charger_dossier_fiscal(source: Path | str) -> DossierFiscalEnregistre:
    chemin = Path(source)
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erreur:
        raise ValueError(f"Dossier fiscal illisible : {chemin.name}") from erreur
    if not isinstance(contenu, dict) or contenu.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Version de dossier fiscal non prise en charge.")

    try:
        client = " ".join(str(contenu["client"]).split())
        annee = int(contenu["annee_fiscale"])
        province = str(contenu["province"])
        sauvegarde_le = str(contenu["sauvegarde_le"])
        documents_json = contenu["documents"]
        donnees_json = contenu["donnees_validees"]
    except (KeyError, TypeError, ValueError) as erreur:
        raise ValueError("Le dossier fiscal enregistré est incomplet.") from erreur

    if not client or annee < 2000 or annee > 2100:
        raise ValueError("Identité du dossier fiscal enregistrée invalide.")
    if province.strip().casefold() not in {"québec", "quebec"}:
        raise ValueError("Cette version accepte uniquement les dossiers Québec.")
    if not isinstance(documents_json, list) or not isinstance(donnees_json, list) or not donnees_json:
        raise ValueError("Le dossier fiscal enregistré ne contient pas de données valides.")

    documents = tuple(Path(str(v)) for v in documents_json)
    donnees = []
    for index, brut in enumerate(donnees_json):
        if not isinstance(brut, dict):
            raise ValueError("Une donnée fiscale enregistrée est invalide.")
        try:
            statut = str(brut["statut"])
            type_document = str(brut["type_document"])
            document = Path(str(brut["document"]))
            case = str(brut["case"])
            libelle = str(brut["libelle"])
            corrigee = bool(brut["corrigee"])
        except KeyError as erreur:
            raise ValueError("Une donnée fiscale enregistrée est incomplète.") from erreur
        if statut not in STATUTS_VALIDATION_AUTORISES:
            raise ValueError("Statut de validation fiscale enregistré invalide.")
        if type_document not in {"T4", "RL-1"}:
            raise ValueError("Type de document fiscal enregistré non pris en charge.")
        ve = _decimal_depuis_json(brut.get("valeur_extraite"), f"valeur_extraite[{index}]")
        vv = _decimal_depuis_json(brut.get("valeur_validee"), f"valeur_validee[{index}]")
        if ve < 0 or vv < 0:
            raise ValueError("Une valeur fiscale enregistrée ne peut pas être négative.")
        donnees.append(DonneeFiscaleValidee(
            document=document,
            type_document=type_document,
            case=case,
            libelle=libelle,
            valeur_extraite=ve,
            valeur_validee=vv,
            corrigee=corrigee,
            statut=statut,
        ))

    dossier = DossierFiscalValide(
        client=client,
        annee_fiscale=annee,
        province="Québec",
        documents=documents,
        donnees_validees=tuple(donnees),
    )

    estimation = None
    e = contenu.get("derniere_estimation")
    if e is not None:
        if not isinstance(e, dict):
            raise ValueError("Le résumé d'estimation enregistré est invalide.")
        estimation = ResumeEstimationSauvegardee(
            resultat=str(e.get("resultat", "")),
            montant=_decimal_depuis_json(e.get("montant"), "estimation.montant"),
            impot_total_preliminaire=_decimal_depuis_json(e.get("impot_total_preliminaire"), "estimation.impot_total_preliminaire"),
            retenues_totales=_decimal_depuis_json(e.get("retenues_totales"), "estimation.retenues_totales"),
        )

    ajustement_reer = _ajustement_reer_depuis_dict(
        contenu.get("ajustement_reer")
    )
    cotisations_syndicales = _cotisations_syndicales_depuis_dict(
        contenu.get("cotisations_syndicales")
    )
    dons_bienfaisance = _dons_bienfaisance_depuis_dict(
        contenu.get("dons_bienfaisance")
    )
    frais_medicaux = _frais_medicaux_depuis_dict(
        contenu.get("frais_medicaux")
    )
    frais_scolarite = _frais_scolarite_depuis_dict(
        contenu.get("frais_scolarite")
    )
    credit_deficience = _credit_deficience_depuis_dict(
        contenu.get("credit_deficience")
    )
    assurance_medicaments = _assurance_medicaments_depuis_dict(
        contenu.get("assurance_medicaments")
    )
    cotisations_excedentaires = _cotisations_excedentaires_depuis_dict(
        contenu.get("cotisations_excedentaires")
    )
    personne_vivant_seule = _personne_vivant_seule_depuis_dict(
        contenu.get("personne_vivant_seule")
    )
    montants_age_retraite = _montants_age_retraite_depuis_dict(
        contenu.get("montants_age_retraite")
    )
    credits_federaux_age_pension = _credits_federaux_age_pension_depuis_dict(
        contenu.get("credits_federaux_age_pension")
    )
    montant_conjoint_federal = _montant_conjoint_federal_depuis_dict(
        contenu.get("montant_conjoint_federal")
    )
    personne_charge_admissible_federale = (
        _personne_charge_admissible_federale_depuis_dict(
            contenu.get("personne_charge_admissible_federale")
        )
    )
    rapport = Path(str(contenu["rapport_pdf"])) if contenu.get("rapport_pdf") else None
    manquants = tuple(x for x in documents if not x.exists())
    return DossierFiscalEnregistre(
        chemin=chemin,
        dossier=dossier,
        sauvegarde_le=sauvegarde_le,
        estimation=estimation,
        rapport_pdf=rapport,
        documents_manquants=manquants,
        ajustement_reer=ajustement_reer,
        cotisations_syndicales=cotisations_syndicales,
        dons_bienfaisance=dons_bienfaisance,
        frais_medicaux=frais_medicaux,
        frais_scolarite=frais_scolarite,
        credit_deficience=credit_deficience,
        assurance_medicaments=assurance_medicaments,
        cotisations_excedentaires=cotisations_excedentaires,
        personne_vivant_seule=personne_vivant_seule,
        montants_age_retraite=montants_age_retraite,
        credits_federaux_age_pension=(
            credits_federaux_age_pension
        ),
        montant_conjoint_federal=(
            montant_conjoint_federal
        ),
        personne_charge_admissible_federale=(
            personne_charge_admissible_federale
        ),
    )


def lister_dossiers_fiscaux(dossier: Path | str = DOSSIERS_FISCAUX_DIR):
    racine = Path(dossier)
    if not racine.exists():
        return ()
    resultats = []
    for chemin in racine.glob("*.json"):
        try:
            resultats.append(charger_dossier_fiscal(chemin))
        except ValueError:
            continue
    return tuple(sorted(resultats, key=lambda x: (x.sauvegarde_le, x.chemin.name), reverse=True))
