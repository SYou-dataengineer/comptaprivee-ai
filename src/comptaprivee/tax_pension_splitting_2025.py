"""2G : dossier de couple indivisible, pensions RPA viagères seulement.

Saisie des deux feuillets appariés de chaque conjoint après validation humaine.
Les limites du profil sont des refus logiciels, pas des règles d'admissibilité.
"""
from dataclasses import dataclass
from decimal import Decimal
from .tax_rules_2025 import (arrondir_cent, impot_federal_brut_2025,
    impot_quebec_brut_2025, montant_personnel_base_federal_2025,
    QUEBEC_BPA_2025, QUEBEC_ABATEMENT_RATE)
from .tax_employment_insurance_2025 import cotisation_fss_prestations_2025
from .tax_federal_age_pension_2025 import (MONTANT_AGE_FEDERAL_MAX_2025,
    SEUIL_REDUCTION_AGE_FEDERAL_2025, TAUX_REDUCTION_AGE_FEDERAL_2025,
    MONTANT_PENSION_FEDERAL_MAX_2025, SEUIL_PREMIERE_TRANCHE_FEDERALE_2025)
from .tax_age_retirement_2025 import (MONTANT_AGE_2025,
    MONTANT_REVENUS_RETRAITE_MAX_2025, COEFFICIENT_REVENUS_RETRAITE_2025,
    SEUIL_REDUCTION_ANNEXE_B_2025, TAUX_REDUCTION_ANNEXE_B_2025)
from .tax_field_extractor import formater_montant_fiscal

ZERO=Decimal('0')


@dataclass(frozen=True)
class ConjointPension2025:
    identifiant: str = ''
    age: int | None = None
    t4a_016: Decimal = ZERO
    rl2_a: Decimal = ZERO
    t4a_022: Decimal = ZERO
    rl2_j: Decimal = ZERO
    source: str = ''
    confirme: bool = False


@dataclass(frozen=True)
class ChoixFractionnement2025:
    cedant: ConjointPension2025 = ConjointPension2025()
    beneficiaire: ConjointPension2025 = ConjointPension2025()
    montant_federal: Decimal = ZERO
    montant_quebec: Decimal = ZERO
    montant_361_cedant: Decimal = ZERO
    choix_conjoint_confirme: bool = False
    annee: int = 2025


@dataclass(frozen=True)
class DeclarationFractionnee2025:
    identifiant: str
    ligne_11500: Decimal
    ligne_11600: Decimal
    ligne_21000: Decimal
    revenu_total_federal: Decimal
    revenu_net_federal: Decimal
    ligne_122: Decimal
    ligne_123: Decimal
    ligne_245: Decimal
    revenu_total_quebec: Decimal
    revenu_net_quebec: Decimal
    montant_30100: Decimal
    montant_31400: Decimal
    montant_361: Decimal
    retenue_43700: Decimal
    retenue_451_avant_transfert: Decimal
    ligne_451_1: Decimal
    ligne_451_3: Decimal
    retenue_quebec: Decimal
    fss_446: Decimal
    impot_federal: Decimal
    impot_quebec: Decimal
    solde: Decimal


@dataclass(frozen=True)
class ResultatFractionnement2025:
    choix: ChoixFractionnement2025
    cedant: DeclarationFractionnee2025
    beneficiaire: DeclarationFractionnee2025
    revenu_familial_quebec: Decimal
    montant_361_couple: Decimal
    retenue_federale_transferee: Decimal
    retenue_quebec_transferee: Decimal


def _montant(v):
    if (not isinstance(v,Decimal) or not v.is_finite() or v<ZERO
            or v>Decimal('999999999.99') or v!=v.quantize(Decimal('.01'))):
        raise ValueError('Montant de fractionnement invalide : fini, non négatif, au cent près.')


def valider_choix_fractionnement_2025(p, *, confirmation_requise=True):
    if not isinstance(p,ChoixFractionnement2025) or type(p.annee) is not int or p.annee!=2025:
        raise ValueError('Dossier de couple 2025 requis.')
    if type(p.choix_conjoint_confirme) is not bool:
        raise ValueError('Confirmation conjointe booléenne requise.')
    for personne in (p.cedant,p.beneficiaire):
        if not isinstance(personne,ConjointPension2025) or type(personne.confirme) is not bool:
            raise ValueError('Données des deux conjoints obligatoires.')
        if any(not isinstance(v,str) for v in (personne.identifiant,personne.source)):
            raise ValueError('Identifiant et source doivent être du texte.')
        if personne.age is not None and (type(personne.age) is not int or not 18<=personne.age<=120):
            raise ValueError('Âge entier de 18 à 120 ans requis pour chaque conjoint.')
        for v in (personne.t4a_016,personne.rl2_a,personne.t4a_022,personne.rl2_j):_montant(v)
        if personne.confirme and (not personne.identifiant.strip() or not personne.source.strip() or personne.age is None):
            raise ValueError('Identité, âge et source des deux conjoints obligatoires.')
        if personne.confirme and personne.t4a_016!=personne.rl2_a:
            raise ValueError('T4A 016 et RL-2 A doivent concorder, sans double compte.')
    for v in (p.montant_federal,p.montant_quebec,p.montant_361_cedant):_montant(v)
    if confirmation_requise or p.choix_conjoint_confirme:
        if not all((p.cedant.confirme,p.beneficiaire.confirme,p.choix_conjoint_confirme)):
            raise ValueError('Confirmez les deux conjoints et le choix commun.')
        if p.cedant.identifiant.strip().casefold()==p.beneficiaire.identifiant.strip().casefold():
            raise ValueError('Deux identifiants de contribuables distincts sont requis.')
        maximum=p.cedant.t4a_016/2
        if p.montant_federal>maximum or p.montant_quebec>maximum:
            raise ValueError('Le transfert de chaque juridiction est limité à 50 % du revenu admissible du cédant.')
        if p.cedant.age<65 and p.montant_quebec:
            raise ValueError('Annexe Q : cédant de 65 ans ou plus requis; transfert fédéral RPA possible avant 65 ans.')
    return p


def calculer_fractionnement_2025(p):
    valider_choix_fractionnement_2025(p)
    c,b=p.cedant,p.beneficiaire
    nf=(c.t4a_016-p.montant_federal,b.t4a_016+p.montant_federal)
    nq=(c.rl2_a-p.montant_quebec,b.rl2_a+p.montant_quebec)
    # Ces bornes écartent les transferts de crédits inutilisés et le montant
    # pour conjoint; le plafond maintient le garde-fou 34990 existant.
    if any(v<Decimal('30000') or v>SEUIL_PREMIERE_TRANCHE_FEDERALE_2025 for v in (*nf,*nq)):
        raise ValueError('Profil limité à 30 000–57 375 $ nets par conjoint dans les deux juridictions : crédits conjugaux/34990 hors périmètre.')
    familial=sum(nq,ZERO)
    retraite=sum((min(MONTANT_REVENUS_RETRAITE_MAX_2025,arrondir_cent(v*COEFFICIENT_REVENUS_RETRAITE_2025)) for v in nq),ZERO)
    ages=sum((MONTANT_AGE_2025 for x in (c,b) if x.age>=65),ZERO)
    reduction=arrondir_cent(max(ZERO,familial-SEUIL_REDUCTION_ANNEXE_B_2025)*TAUX_REDUCTION_ANNEXE_B_2025)
    disponible=max(ZERO,ages+retraite-reduction)
    if p.montant_361_cedant>disponible:
        raise ValueError('Répartition 361 supérieure au montant commun après réduction unique de l’annexe B.')
    rf=arrondir_cent(c.t4a_022*p.montant_federal/c.t4a_016)
    rq=arrondir_cent(c.rl2_j*p.montant_quebec/c.rl2_a)
    declarations=[]
    for i,x in enumerate((c,b)):
        age=max(ZERO,MONTANT_AGE_FEDERAL_MAX_2025-arrondir_cent(max(ZERO,nf[i]-SEUIL_REDUCTION_AGE_FEDERAL_2025)*TAUX_REDUCTION_AGE_FEDERAL_2025)) if x.age>=65 else ZERO
        pension=min(MONTANT_PENSION_FEDERAL_MAX_2025,nf[i])
        credits=arrondir_cent((montant_personnel_base_federal_2025(nf[i])+age+pension)*Decimal('.145'))
        base=max(ZERO,impot_federal_brut_2025(nf[i])-credits)
        federal=base-arrondir_cent(base*QUEBEC_ABATEMENT_RATE)
        m361=p.montant_361_cedant if i==0 else disponible-p.montant_361_cedant
        qc=impot_quebec_brut_2025(nq[i])-arrondir_cent(QUEBEC_BPA_2025*Decimal('.14'))-arrondir_cent(m361*Decimal('.14'))
        if qc<ZERO:
            raise ValueError('Crédits Québec inutilisés/transfert 431 hors périmètre; révisez la répartition 361.')
        retenue_f=x.t4a_022+(-rf if i==0 else rf)
        retenue_q=x.rl2_j+(-rq if i==0 else rq)
        fss=cotisation_fss_prestations_2025(nq[i])
        declarations.append(DeclarationFractionnee2025(x.identifiant,x.t4a_016,
            p.montant_federal if i else ZERO,p.montant_federal if not i else ZERO,
            x.t4a_016+(p.montant_federal if i else ZERO),nf[i],x.rl2_a,
            p.montant_quebec if i else ZERO,p.montant_quebec if not i else ZERO,
            x.rl2_a+(p.montant_quebec if i else ZERO),nq[i],age,pension,m361,
            retenue_f,x.rl2_j,rq if not i else ZERO,rq if i else ZERO,retenue_q,fss,
            federal,qc,arrondir_cent(federal+qc+fss-retenue_f-retenue_q)))
    return ResultatFractionnement2025(p,*declarations,familial,disponible,rf,rq)


def lignes_fractionnement_2025(r):
    f=formater_montant_fiscal
    lignes=['FRACTIONNEMENT DE PENSION 2025 - DOSSIER DE COUPLE',
        'Estimation locale; validation comptable obligatoire. Ce rapport ne remplace pas les formulaires signés.',
        'RPA viagères uniquement; Canada/Québec et union toute l’année; assurance médicaments privée complète.',
        f'T1032 21000 = 11600 : {f(r.choix.montant_federal)}',
        f'Annexe Q 245 = 123 : {f(r.choix.montant_quebec)}',
        f'Retenues transférées fédérales / Québec : {f(r.retenue_federale_transferee)} / {f(r.retenue_quebec_transferee)}',
        f'Annexe B : revenu familial {f(r.revenu_familial_quebec)}; montant 361 commun {f(r.montant_361_couple)}']
    for titre,d,p in [('CÉDANT',r.cedant,r.choix.cedant),('BÉNÉFICIAIRE',r.beneficiaire,r.choix.beneficiaire)]:
        lignes += ['',f'{titre} : {d.identifiant}; âge : {p.age}; source : {p.source}']
        for libelle,champ in [('11500','ligne_11500'),('11600','ligne_11600'),('21000','ligne_21000'),('15000','revenu_total_federal'),('23600 / 26000','revenu_net_federal'),('122','ligne_122'),('123','ligne_123'),('245','ligne_245'),('199','revenu_total_quebec'),('275 / 299','revenu_net_quebec'),('30100','montant_30100'),('31400','montant_31400'),('361','montant_361'),('43700 après transfert','retenue_43700'),('451 avant transfert','retenue_451_avant_transfert'),('451.1','ligne_451_1'),('451.3','ligne_451_3'),('Retenue Québec nette','retenue_quebec'),('446 FSS','fss_446'),('Impôt fédéral après abattement','impot_federal'),('Impôt Québec','impot_quebec'),('Solde (+ à payer / - remboursement)','solde')]:
            lignes.append(f'{libelle} : {f(getattr(d,champ))}')
    return lignes+['','LIMITES : aucun autre revenu, PSV/RRQ/AE/RQAP, salaire, déduction, crédit particulier, décès, revenu étranger, FERR ou RAMQ publique.',
        'Choix manuel, sans optimisation; deux nets de 30 000 à 57 375 $, garde-fou 34990 conservé.',
        'Aucune donnée transmise; conserver les pièces et les choix signés T1032/annexe Q.']
