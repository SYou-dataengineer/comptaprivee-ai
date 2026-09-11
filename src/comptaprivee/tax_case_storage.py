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
