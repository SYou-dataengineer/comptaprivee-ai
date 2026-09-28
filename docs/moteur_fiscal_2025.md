# Moteur fiscal 2025 — inventaire et blocs fonctionnels

Audit du code au 15 septembre 2026, après le Bloc 2 de l'interface.
Cet inventaire porte sur le calcul réellement orchestré, pas seulement sur
la présence de fichiers ou de boutons. Le logiciel produit une estimation
locale; il ne constitue pas encore une déclaration T1/TP-1 complète.

## Couverture constatée avant ce bloc

| Domaine | Couverture effective | Limites importantes |
| --- | --- | --- |
| Revenus | Emploi Québec : un T4 et un RL-1; revenus fédéral et Québec distincts, retenues et cotisations rapprochées | Le calcul refuse plusieurs T4/RL-1; autres sources de revenus absentes |
| Déductions | RRQ supplémentaire, déduction québécoise pour travailleur, REER/RPAC/RVER ordinaire, cotisations syndicales/professionnelles au fédéral | Plafond REER confirmé manuellement; transferts et RAP/REEP exclus |
| Impôt de base | Barèmes fédéral/Québec, montants personnels, crédit canadien pour emploi, cotisations sociales fédérales, abattement Québec et rapprochement des retenues | Profil salarié simple; pas de calcul général d'impôt minimum ou d'impôt étranger |
| Crédits personnels fédéraux | Âge, conjoint, personne à charge admissible, aidants 30425/30450/enfant, achat d'habitation, accessibilité | Garde-fous au-delà de la première tranche faute de ligne 34990; plusieurs combinaisons familiales refusées |
| Crédits fédéraux et Québec | Frais médicaux, scolarité, handicap/déficience, dons | Admissibilité et montants confirmés; reports, transferts et cas avancés incomplets |
| Québec | Cotisations professionnelles, personne vivant seule, âge/retraite, assurance médicaments, excédents RRQ/AE/RQAP | Annexe B combinée sans conjoint livrée en 6A; combinaison avec conjoint à intégrer; assurance médicaments limitée à certains profils |
| Pensions | Fonctions de calcul de crédits présentes | La ligne fédérale 31400 est explicitement bloquée dans l'orchestrateur : les revenus de pension ne sont pas encore intégrés; présence du module ≠ prise en charge d'un retraité |
| Chaîne applicative | Validation humaine, dossier verrouillé, sauvegarde JSON/rechargement, résumé, trace et PDF, tests Tkinter | L'extraction initiale concerne les cases reconnues du T4/RL-1; les autres feuillets nécessitent de futurs blocs |

Fichiers de référence : `tax_engine_input_2025.py`, `tax_income_2025.py`,
`tax_estimation_2025.py`, `tax_reconciliation_2025.py`, `tax_*_2025.py`,
`tax_field_extractor.py`, `tax_case_storage.py` et leurs tests.

## Principaux manques et ordre proposé

Chaque ligne représente une famille à découper en blocs vérifiables. La mission
de finalisation autorise désormais leur enchaînement autonome après validation,
commit et push; arrêt seulement pour une décision ou un blocage réel.

| Priorité | Famille | Fonctionnalités et dépendances à traiter |
| --- | --- | --- |
| 1 — présent bloc | Déductions du salarié | RPA services courants, fédéral 20700 / Québec 205; complète directement le profil T4/RL-1 |
| 2 | Revenus de remplacement et retraite | AE/RQAP et remboursements éventuels; RRQ/RPC, PSV et récupération, pensions/FERR/REER, revenus admissibles aux crédits de retraite; autres prestations et déductions correspondantes |
| 3 | Revenus de placement | Intérêts, dividendes déterminés/ordinaires et crédits associés, gains/pertes en capital et reports; FSS, frais de placement/annexe N et impôts étrangers selon profil |
| 4 | Déductions restantes | CELIAPP, frais de garde fédéraux, emploi/T2200, déménagement, frais financiers, pension alimentaire, autres déductions; justificatifs et plafonds propres à chaque régime |
| 5 | Crédits fédéraux restants et intégration | Ligne 34990 pour lever les garde-fous justifiés, intérêts sur prêts étudiants, formation, crédits remboursables (ACT, supplément médical), transferts et reports de scolarité/dons, combinaisons familiales |
| 6 | Crédits Québec restants et intégration | Frais de garde, personne aidante, solidarité, prime au travail, soutien/maintien à domicile des aînés, prolongation de carrière, achat d'habitation, intérêts étudiants; annexe B combinée et transferts familiaux |
| 7 | Profils avancés | Employeurs multiples et proratisations, travail autonome/RRQ/RQAP, location/DPA, pertes, résidence partielle/interprovinciale, décès, impôt minimum, déclarations de biens étrangers |

Cet ordre privilégie les bases de revenu dont dépendent les crédits. Les
cotisations et récupérations liées aux nouveaux revenus devront être traitées
dans le même bloc ou entraîner un refus explicite du profil non couvert.
Les contrôles existants de la ligne 34990 restent en place jusqu'à son propre bloc.

Référentiels de couverture :

- [ARC — types de revenus](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/types-income.html).
- [Revenu Québec — déclaration, guide et annexes 2025](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/details-courant/tp-1/).

## Bloc fiscal 1 — cotisations RPA pour services courants

### Règles et sources officielles consultées le 15 septembre 2026

- [ARC — ligne 20700](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-20700-deduction-regimes-pension-agrees.html)
  (page du 20 janvier 2026) : déduction des cotisations admissibles figurant
  notamment sur le T4 case 20 ou les reçus RPA. Les services avant 1990 ont
  des règles distinctes; leur seuil de 3 500 $ ne plafonne pas les services courants.
- [Revenu Québec — ligne 205](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-205/)
  : généralement case D du RL-1; la déduction pour services courants ne peut
  dépasser celle de la ligne fédérale 20700. Les conventions de retraite,
  services anciens et transferts ont des traitements distincts.
- [ARC — guide T4040, édition 2025](https://www.canada.ca/fr/agence-revenu/services/formulaires-publications/publications/t4040/reer-autres-regimes-enregistres-retraite.html)
  : cases T4 74/75 pour certains services antérieurs à 1990.

### Périmètre et décisions

- Cotisations personnelles à un RPA canadien, services courants de 2025
  uniquement, confirmées avec leurs pièces par le comptable. Les rachats
  (même après 1989), reports, transferts, conventions de retraite et régimes
  étrangers sont exclus **par périmètre logiciel**, pas déclarés non déductibles.
- Montants fédéral et Québec conservés séparément; Québec ≤ fédéral.
  Les T4/RL-1 ne sont jamais additionnés entre eux pour cette déduction.
- Extraction des cases T4 20/74/75 et RL-1 D/D-1/D-2/D-3. Les marqueurs explicites
  « case », « box » ou « code » sont nécessaires selon la règle; la vérification
  humaine des feuillets reste nécessaire, notamment pour les tableaux OCR.
- Si une case 20/D est présente et validée, le profil RPA doit correspondre
  exactement à son montant. Une omission bloque l'estimation. Les cases
  spéciales positives bloquent le profil courant, même sans profil RPA saisi.
- La saisie manuelle documentée reste possible lorsqu'aucune case RPA n'a été
  extraite. Elle représente le total admissible; elle ne s'ajoute pas aux cases.
- Déduction appliquée avant REER et crédits liés au revenu; revenu total,
  cotisations RRQ/AE/RQAP, salaire et plafond individuel REER inchangés.
- Montants `Decimal` finis, non négatifs et au cent près; pas d'arrondi de saisie
  silencieux. Capacité de saisie : 999 999 999,99 $ (limite technique, non fiscale).
- Ancien JSON sans champ RPA : profil vide. Nouveau profil : validation stricte
  des montants, confirmations et sources; sauvegarde/recalcul cohérents.
- GUI défilable existante réutilisée; modification RPA invalide l'estimation
  et le lien PDF. Un ancien résultat ouvert ne peut plus exporter un rapport périmé.
- Résumé, trace et PDF détaillent les deux déductions, leurs pièces et le périmètre.

Aucune règle fiscale déjà validée n'est remplacée dans ce bloc. L'ajout RPA
est justifié par les lignes officielles ci-dessus. Les corrections de contrôle
concernent la nouvelle saisie, les limites de lecture entre cases et l'export
d'une estimation devenue périmée.

### Validation

Cas de référence : salaire 52 000 $, RPA de 3 000 $ dans les deux juridictions.
Revenu net fédéral : 48 515 $; Québec : 47 095 $; remboursement estimé :
6 394,28 $, contre 5 611,05 $ sans RPA. Vérifications supplémentaires :
montants distincts, absence de plafond de 3 500 $ sur les services courants,
non-finis/négatifs, doublons, cas exclus, JSON corrompu/ancien, calcul après
rechargement, interactions REER/cotisations syndicales/frais médicaux, GUI
à deux tailles et trois facteurs Tk, invalidation d'un ancien export.

Les journaux et captures de démonstration restent dans `tmp/`, exclus de Git.
Les limites de DPI Windows réels, thèmes et multi-écrans du Bloc 2 restent ouvertes.

Résultat final local : **1 649 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation, en 41,78 s (`python -m pytest -q`).
**72 nouveaux cas** : 66 tests de règles/extraction/intégration/persistance/PDF
et 6 parcours ou combinaisons Tkinter. Le profil nul conserve la référence
antérieure de 5 611,05 $ de remboursement.

Formulaire inspecté à 600 × 400 et 1 000 × 700, en haut et en bas du défilement.
Les deux pages du rapport fictif ont été rendues avec PyMuPDF et inspectées;
un test vérifie également les limites de page avec une source de 1 000 caractères.
La saisie depuis un profil vide, la restauration du profil et le refus d'un
export périmé sont exercés par les tests GUI.

Un lancement intermédiaire a rencontré `invalid command name "tcl_findLibrary"`
à la création d'une racine Tk d'un test existant du Bloc 1. Cette intermittence
Windows, déjà observée au Bloc 2, n'est pas déclarée corrigée : le lancement
complet final a réussi sans contournement, retrait ou désactivation de tests.
La surveillance de l'environnement Tcl et les avertissements de dépréciation
restent ouverts; ils ne justifient aucune modification des règles fiscales.

## Priorité 2 — audit des revenus de remplacement et de retraite

Audit du 15 septembre 2026, à partir du bloc RPA validé (`e746059`).
La priorité 2 est une famille de blocs, pas un unique ajout de revenu.
Avant ce travail, seul le salaire alimente réellement les revenus totaux;
les crédits d'âge existent, mais cela ne permet pas de déclarer une pension.
Les règles RPA et les règles fiscales précédemment validées sont conservées.

### Cartographie des lignes et dépendances

| Bloc | Feuillets / données à intégrer | Fédéral | Québec | Dépendances et limites à traiter ensemble |
| --- | --- | --- | --- | --- |
| **2A — présent bloc : RQAP ordinaire** | T4E 14/36, 22/23, 30; RL-6 A/D/G | 11900; 11905 comme sous-ensemble informatif; 23200; retenues 43700 | 110; 246; retenues 451; FSS 446 | Appariement sans double compte, revenu net des crédits, annexe F; remboursements de prestations de 2025 seulement |
| 2B — assurance-emploi | T4E 7, 14, 15, 17, 18, 20, 21, 22, 23, 26, 27, 30, 33, 37 | 11900; sous-ensemble 11905 pour maternité/parentales; 23200; 23500 et 42200 si récupération; 25600 pour l'aide non imposable | 111; 246 pour trop-payé remboursé; 250 point 3 pour récupération fédérale; 451; FSS 446 | Séparer AE du RQAP; calcul de récupération après les déductions; seuil AE 2025 de 82 125 $, taux et exemptions du feuillet; exonérations et paiements rétroactifs distincts |
| 2C — RRQ/RPC | T4A(P) 20, sous-cases de prestations dont invalidité 16; RL-2 C; retenues correspondantes | 11400; 11410 informatif si invalidité; 43700 | 119; 451; FSS 446 | Retraite, survivant, enfant et invalidité; attribution au bénéficiaire; paiements rétroactifs; ne pas confondre avec les cotisations RRQ sur salaire |
| 2D — PSV et suppléments | T4A(OAS) 18, 19, 20, 21, 22, 23 selon leur fonction | 11300; 14600; 25000; récupération 23500/42200; retenues 43700 | 114; 148; 295; 250 point 3; 451 | Seuil PSV 2025 de 93 454 $, revenu de récupération ajusté et plafond; distinguer récupération et impôt retenu; interaction AE; prestations non admissibles au crédit de pension |
| 2E — pensions, FERR et rentes | T4A 016, 024, 133, 194; T4RIF 16/22; T3 31; T5 19; RL-2 A/B et codes complémentaires | 11500 ou 13000/12100 selon la nature, l'âge et le décès du conjoint; 31400 pour la portion admissible | 122 ou autre ligne selon nature; 361 selon admissibilité; FSS 446 | Âge au 31 décembre, type de régime, admissibilité distincte au crédit; revenus étrangers et décès à traiter séparément; le FSS exige une assiette complète |
| 2F — retraits REER et sommes forfaitaires | T4RSP 16/18/20/22/26/28/34; T4A 018/106; T4 66/67; RL-2 B et codes | 12900 ou 13000; certaines sommes négatives à 23200; retenues | 122 ou 154 selon nature; retenues 451 | Attribution au conjoint, remboursement de primes, décès, transferts et RAP/REEP; un retrait ordinaire n'est pas automatiquement un revenu admissible au crédit de pension |
| 2G — fractionnement de pension | T1032, annexe Q et données des deux conjoints | Revenu reçu 11600, déduction du cédant 21000; répartition des retenues | Revenu reçu 123, déduction 245; répartition des retenues | Deux déclarations cohérentes, conditions d'âge/admissibilité propres aux deux juridictions; influence des crédits, PSV, RAMQ et FSS |
| 2H — autres prestations de remplacement | T5007, RL-5 et renseignements CNESST/SAAQ; T4A pour certaines autres prestations | 14400/14500, déduction 25000 selon nature | 147/148, déduction 295; redressement 358 et annexe E selon indemnité | Inclusion au revenu net malgré une déduction au revenu imposable, attribution conjugale de certaines aides, indemnités et remboursements; ne pas traiter comme un revenu salarial |

Les lignes 11905 et 11410 sont des renseignements compris dans une autre
ligne de revenu : elles ne s'ajoutent jamais une seconde fois au revenu total.
Les remboursements volontaires de trop-payés (23200/246) sont distincts des
récupérations calculées sur la déclaration (23500/42200 et Québec 250 point 3).
La ligne Québec 123 concerne le fractionnement, pas les retraits REER ordinaires.

Les revenus nouveaux doivent précéder RPA, REER et cotisations syndicales
dans le calcul du revenu net. Les crédits médicaux, d'âge et familiaux ainsi
que la RAMQ doivent ensuite utiliser les nouvelles bases; les profils saisis
manuellement avec un ancien revenu net doivent être revalidés. Le salaire
demeure la base des cotisations salariales et du crédit canadien pour emploi.
L'ACT, la prime au travail, les frais de garde et les autres prestations liées
au revenu restent dans les priorités ultérieures : leur assiette de revenu
gagné devra distinguer salaire, RQAP, AE et pension selon chaque dispositif.

### Références officielles de l'audit

- [ARC — guide fédéral 2025, tableau des revenus de retraite](https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/5000-g.html#h-18) : feuillets, cases, âge, décès et lignes fédérales.
- [ARC — T4E et ses cases](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/tax-slips/understand-your-tax-slips/t4-slips/t4e-statement-employment-insurance-other-benefits.html).
- [ARC — ligne 11900](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-11900-employment-insurance-other-benefits.html) et [ligne 11905](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-11900-employment-insurance-other-benefits/line-11905-employment-insurance-maternity-and-parental-benefits-and-provincial-parental-insurance-plan-maternity-and-paternity-benefits.html).
- [ARC — remboursement de prestations, ligne 23500](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-23500-social-benefits-repayment.html) et [PSV 2025](https://www.canada.ca/en/services/benefits/publicpensions/old-age-security/repayment.html).
- [Revenu Québec — déclaration et annexes 2025](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/details-courant/tp-1/), [RL-6](https://www.revenuquebec.ca/documents/fr/formulaires/rl/RL-6%282022-10%29.pdf), [ligne 110](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-110/) et [ligne 111](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-111/).
- Revenu Québec : [PSV 114](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-114/), [RRQ/RPC 119](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-119/), [pensions et REER 122](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-122/), [fractionnement 123](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-123/).
- Revenu Québec : [indemnités et suppléments 148](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-148/), [déductions 295](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/276-a-298-2-revenu-imposable/ligne-295/), [remboursements 246](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-246/) et [récupération 250 point 3](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-250/point-3/).

## Bloc fiscal 2A — RQAP ordinaire et FSS 2025

### Règles intégrées et périmètre

- Un T4E et un RL-6 distincts, du même bénéficiaire et pour 2025, en complément
  du profil salarié existant (un T4 et un RL-1). Résidence Canada/Québec toute
  l'année, sans exonération, rétroactivité ou autre prestation T4E.
- Les trois cases T4E 14, T4E 36 et RL-6 A sont obligatoires et doivent être
  égales. Les retenues T4E 23/RL-6 G et remboursements T4E 30/RL-6 D doivent
  concorder exactement. Aucun cumul de deux feuillets pour une même somme.
- Remboursement limité aux prestations de 2025 déjà incluses, sans dépasser
  leur montant. Les remboursements d'années antérieures restent exclus :
  les lignes 246 et 462 point 8 prévoient des traitements particuliers.
- Les cases facultatives non extraites ne valent zéro qu'après confirmation
  comptable de la revue des feuillets complets. Les doublons, montants
  non finis, négatifs ou avec fractions de cent et les sources incohérentes
  sont refusés. Les cases T4E de prestations hors profil positives bloquent.
- L'extraction reconnaît les marqueurs explicites « case »/« box »; elle ne
  prétend pas lire toutes les dispositions de tableaux OCR. Le contrôle
  humain couvre le nom du bénéficiaire, l'année, les feuillets remplacés et
  les cases omises. Aucun montant supplémentaire n'est saisi dans le
  formulaire de confirmation : la correction reste dans la validation des cases.
- Revenu total augmenté du brut; déductions 23200/246 appliquées avant les
  déductions et crédits existants. Les retenues RQAP s'ajoutent aux retenues
  salariales; la base d'emploi et les cotisations salariales restent intactes.

### Dépendance FSS traitée dans ce bloc

L'[annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf)
exclut le salaire mais ne soustrait pas les prestations RQAP. Dans le présent
périmètre, son assiette est donc le RQAP brut moins le remboursement admissible
de la ligne 246. RPA et REER ne figurent pas dans les déductions de cette annexe.

- Assiette ≤ 18 130 $ : zéro.
- Jusqu'à 63 060 $ : 1 % de l'excédent sur 18 130 $, plafonné à 150 $.
- Au-delà de 63 060 $ : 150 $ + 1 % de l'excédent sur 63 060 $, plafonné à 1 000 $.

La cotisation est arrondie au cent et ajoutée au rapprochement Québec,
sans abattement fédéral et sans réduction du revenu net. Il s'agit d'une
extension pour ce profil; ce calcul ne prétend pas couvrir une annexe F
contenant des revenus de placement, pensions ou autres déductions.

### Chaîne applicative et validation

La reconnaissance distingue T4E/RL-6 du salaire. La GUI présente les montants
consolidés et la confirmation du périmètre. Toute nouvelle extraction ou
modification des données retire cette confirmation et invalide le résultat
et le PDF. La confirmation et les cases sont sauvegardées en JSON; un ancien
dossier sans confirmation demeure chargeable mais exige une validation RQAP
avant calcul s'il contient ces feuillets. La trace, le résumé et le PDF
identifient les lignes, l'absence de double compte et la cotisation FSS.

Cas fictif de référence : salaire 52 000 $, prestations 20 000 $, remboursement
de prestations de 2025 de 1 000 $, retenues RQAP fédérales 1 800 $ et Québec
2 200 $. Revenus totaux 72 000 $, nets fédéral 70 515 $ et Québec 69 095 $;
retenues totales 17 700 $; FSS 8,70 $. Avec RPA 3 000 $, REER 5 000 $ et
cotisations syndicales fédérales 600 $, revenus nets 61 915 $ et 61 095 $;
le FSS demeure 8,70 $.

Au terme du bloc 2A, les blocs 2B à 2H restaient à développer après accord utilisateur. Aucun crédit
de retraite précédemment bloqué n'est activé par ce bloc RQAP.

Validation finale locale : **1 726 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation, en 53,04 s (`python -m pytest -q`).
Les **77 nouveaux cas** comprennent 68 tests de calcul, extraction, validation,
persistance, trace/PDF et interactions avec les crédits, ainsi que 9 parcours
ou combinaisons GUI. Les tests ciblés passent également (77/77).

Le parcours de reconnaissance compte séparément T4E et RL-6 parmi les feuillets
reconnus. La préparation bloque un T4E/RL-6 reconnu sans cases, un feuillet
identifié par son nom mais illisible, ainsi qu'un document ajouté sans étape
de reconnaissance. Ces contrôles évitent une estimation fondée sur le seul
salaire après omission des prestations.

Le formulaire a été inspecté à 600 × 400 et 1 000 × 700; les actions sont
testées à trois facteurs Tk. Les deux pages du PDF fictif ont été rendues
et inspectées. Résultat du cas de référence : impôt total 14 508,39 $,
remboursement estimé 3 191,61 $. Captures et journaux restent dans `tmp/`,
exclus du commit. Les limites OCR, profils multiples, années antérieures,
DPI Windows réels et avertissements de dépréciation restent documentées.

## Bloc 2B — Assurance-emploi 2025

### Périmètre et exclusions

Le profil couvre un unique T4E validé, en complément du profil salarié Québec
T4/RL-1 existant, pour le même bénéficiaire résidant au Canada et au Québec
toute l'année 2025. La confirmation comptable du feuillet complet est obligatoire.
Les cases 7 (taux de 0 % ou 30 %) et 14 sont requises. Les cases facultatives
15, 22, 23, 26, 27, 30 et 37 absentes sont nulles seulement après cette revue.
La case 37 est comprise dans la case 14 et ne crée aucun revenu supplémentaire.

Les montants doivent être finis, non négatifs, au cent près et inférieurs à
un milliard de dollars. Sources non jointes, statuts non validés, cases en
double et T4E multiples sont refusés. Les cases 15 + 37 ne peuvent dépasser
14; le remboursement 30 ne peut dépasser 14. Si 26 ou 27 est présente,
leur somme doit égaler 30, sans additionner ces sous-cases une seconde fois.

Sont exclus : combinaison AE/RQAP (dont RL-6 ou T4E 36), retraite et PSV,
ajustements PUGE/REEI, aide aux études, exonérations, paiements rétroactifs,
remboursements de prestations d'années antérieures et autres revenus hors
profil. Toute case non autorisée non nulle bloque le calcul, notamment
17, 18, 20, 21, 24 et 33. La ligne 25600 de la cartographie d'audit n'est donc
pas implémentée par ce bloc. Le taux du feuillet et ses exemptions sont
contrôlés par le comptable, pas reconstitués à partir d'un historique d'AE.

### Calcul et sources

Les références ARC T4E, 11900/11905 et 23500 citées dans l'audit ci-dessus
ainsi que l'annexe F 2025 ont été revérifiées le 16 septembre 2026.
Le brut 14 alimente 11900 et Québec 111; 37 renseigne 11905. Le remboursement
30 est déduit à 23200/246 avant les déductions RPA, REER et syndicales.
Après ces déductions, le revenu fédéral avant récupération représente 23400
dans ce périmètre sans ajustements PUGE/REEI ni PSV.

Pour un taux de 30 %, la récupération est arrondie au cent :
`30 % × min(max(0, case 15 − case 30), max(0, ligne 23400 − 82 125))`.
Elle est nulle pour un taux de 0 %. Elle réduit le revenu net et imposable
à 23500 et Québec 250 point 3, avant les crédits, et s'ajoute au montant
fédéral à payer à 42200 sans abattement Québec. Les retenues 22 et 23
s'ajoutent respectivement à 43700 et Québec 451.

L'assiette FSS est `case 14 − case 30 − récupération`, conformément aux
déductions 246 et 250 point 3 de l'annexe F. Le barème documenté au bloc 2A
s'applique; les déductions RPA/REER ne diminuent pas cette assiette.
Ce calcul reste limité aux revenus du présent profil.

### Intégration et vérification

Reconnaissance, extraction, validation, confirmation GUI, estimation, trace,
JSON et PDF utilisent le même profil AE. Une nouvelle extraction retire les
confirmations; une modification du profil invalide l'estimation et son export.
La confirmation persiste au rechargement. Un ancien JSON sans `ae_confirme`
reste chargeable mais exige une confirmation avant calcul avec T4E AE.
Un T4E reconnu sans cases ne peut être silencieusement omis à la préparation.

Cas fictif : salaire 52 000 $, T4E 14 = 40 000 $, 15 = 30 000 $, 37 = 5 000 $,
30 = 1 000 $, taux 30 %, retenues 22 = 2 500 $ et 23 = 3 000 $.
Revenu avant récupération : 90 515 $; récupération : 2 517 $; revenus nets
fédéral 87 998 $ et Québec 86 578 $; FSS 150 $; impôt total 23 481,10 $;
retenues 19 200 $; solde estimé 4 281,10 $. Avec RPA 3 000 $, REER 5 000 $
et cotisations syndicales 600 $, le revenu avant récupération est 81 915 $
et la récupération nulle. Le profil RQAP conserve son remboursement de 3 191,61 $.

Les 142 tests ciblés AE/RQAP passent, dont 65 nouveaux cas AE (58 tests de
règles et d'intégration et 7 cas GUI). Le formulaire a été inspecté à
600 × 400 et 1 000 × 700 en haut et en bas; les actions sont aussi testées
à trois facteurs Tk. Les deux pages PDF ont été rendues avec PyMuPDF et
inspectées : aucun texte tronqué ni chevauchement constaté. Captures, PDF
fictif et scripts de vérification restent dans `tmp/`, exclus du commit.

Limites restantes : extraction OCR avec marqueurs explicites case/box,
revue humaine des omissions et du bénéficiaire, profils exclus ci-dessus,
DPI Windows réels, thèmes et multi-écrans. Aucun crédit de retraite n'est
activé. À la clôture du Bloc 2B, le Bloc 2C attendait l'accord utilisateur.

Validation finale locale : **1 791 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation, en 49,06 s (`python -m pytest -q`, Python
de `.venv`). Les premiers essais dans le bac à sable ont rencontré des refus
d'accès aux dossiers temporaires et à Tk; les tests ciblés puis la suite
complète ont réussi avec les accès Windows nécessaires, sans désactivation
ni modification des tests. Les avertissements PyMuPDF/SWIG et openpyxl ainsi
que l'intermittence Tcl déjà documentée restent à surveiller.

## Bloc 2C — Prestations RRQ/RPC 2025

### Sources officielles vérifiées le 16 septembre 2026

- [ARC, T4A(P)](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/tax-slips/understand-your-tax-slips/t4-slips/t4a-p-statement-canada-pension-plan-benefits.html) : 14 retraite, 15 survivant, 16 invalidité, 17 enfant, 18 décès et 19 après-retraite sont comprises dans le total 20. La case 22 est la retenue fédérale (43700); 21 et 23 sont des nombres de mois, pas des revenus.
- [ARC, 11400 et 11410, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-11400-cpp-qpp-benefits.html) : total 20 à 11400; invalidité 16 à 11410 sans nouvel ajout. La rente d'enfant se déclare chez l'enfant, même si le parent reçoit le paiement. Une prestation de décès suit un traitement distinct; les arrérages peuvent nécessiter un calcul fiscal sur les années antérieures. L'invalidité peut affecter les droits REER, que ce module ne recalcule pas.
- [Revenu Québec, 119](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-119/) : retenir RL-2 C ou le T4A(P) si aucun RL-2 n'a été reçu; même attribution à l'enfant. Une rente mensuelle de survivant n'est pas une prestation forfaitaire de décès.
- [Guide RL-2](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/rl-2-g/guide-du-releve-2-revenus-de-retraite-et-rentes/) et [Québec 451](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/451-a-480-remboursement-ou-solde-a-payer/ligne-451/) : la case C peut aussi désigner d'autres régimes; la provenance RRQ/RPC doit être confirmée. La retenue Québec provient de J.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : dans ce profil sans autres revenus ni remboursements, l'assiette correspond aux prestations RRQ/RPC. Le salaire est soustrait, pas les déductions RPA/REER. Barème du Bloc 2A : exemption 18 130 $, palier 63 060 $, plafonds 150 $ et 1 000 $. [Ligne 446](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/400-a-447-impot-et-cotisations/ligne-446/) : les paiements rétroactifs exigent potentiellement un traitement FSS distinct, exclu ici.
- [ARC 31400](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-31400-pension-income-amount.html) et [Québec 361](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/350-a-398-1-credits-dimpot-non-remboursables/ligne-361/) : RRQ/RPC non admissible au montant pour revenus de pension/retraite. Les crédits d'âge restent distincts, soumis aux validations et limites existantes.
- [Cotisations du salarié au RRQ](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/payer-ou-etre-rembourse/paiement-des-cotisations/cotisations-du-salarie/cotisation-du-salarie-au-regime-de-rentes-du-quebec/) : invalidité, âge et choix de cesser de cotiser peuvent modifier les cotisations. Le bloc ne calcule pas ces proratisations ou élections.

### Périmètre implémenté

Un T4A(P) obligatoire, au plus un RL-2 distinct et concordant, même bénéficiaire,
résident Canada/Québec toute l'année. Retraite, survivant et après-retraite
ordinaires, avec ou sans le profil salarial existant. Invalidité et rente
d'enfant prises en charge sans salaire; le dossier est celui du bénéficiaire,
donc de l'enfant pour la case 17. Aucun T4/RL-1 fictif n'est créé sans emploi;
cotisations, déductions salariales et montant canadien pour emploi sont nuls.

La confirmation `rrq_rpc_confirme` couvre les feuillets complets, leur année,
leur bénéficiaire, la provenance du RL-2 et l'absence des situations exclues.
Les cases facultatives non extraites sont nulles seulement après cette revue.
Les sous-cases peuvent ne pas détailler tout le total; leur somme ne peut
jamais le dépasser. Total 20 obligatoire; C obligatoire et égal à 20 si RL-2
présent. Les retenues 22/J sont indépendantes, chacune ajoutée une fois.
Moins de 13 mois entiers pour 21/23; montants finis, non négatifs, au cent près,
au plus 999 999 999,99 $. Sources absentes, doublons, statuts non validés et
feuillets multiples sont refusés.

Refus explicites : case 18 positive, autres cases monétaires RL-2 hors C/J,
codes complémentaires non nuls, AE/RQAP/PSV ou autres feuillets combinés,
invalidité ou enfant avec salaire, sous-types mixtes avec rente d'enfant,
incohérences entre feuillets et confirmation manquante. Rétroactivité,
remboursements, décès du déclarant, exonérations, partage de rente et autres
profils complexes sont exclus par la confirmation obligatoire : le moteur
ne prétend pas les détecter à partir des seuls montants extraits. Les contrôles
humains restent essentiels, notamment pour une case 20 sans sous-cases.

Les prestations augmentent les revenus avant RPA/REER et les crédits.
Le FSS est ajouté au rapprochement Québec, sans abattement fédéral ni
déduction du revenu net. Aucun crédit de pension 31400/361 n'est activé.
La réception d'une rente d'invalidité ne vaut pas admissibilité automatique
au crédit pour handicap. Les plafonds REER, primes RAMQ et autres crédits
restent gérés par leurs profils existants, avec leurs confirmations requises.
Les refus existants liés à 34990 et aux hauts revenus sont conservés.

### Parcours applicatif et résultats de référence

Classification distincte T4A(P)/RL-2, extraction avec marqueurs case/box,
validation comptable, formulaire défilant, calcul, sauvegarde/rechargement,
résumé, trace et PDF sont intégrés. La préparation refuse un feuillet reconnu
sans cases. Une nouvelle extraction retire la confirmation; un changement
de profil invalide l'estimation et son PDF. L'ancien JSON sans confirmation
reste chargeable et exige la revue avant calcul RRQ/RPC.

Cas salarié fictif : salaire 52 000 $, prestations 20 000 $, retenues
RRQ/RPC 1 800 $ fédéral et 2 200 $ Québec. Revenus totaux 72 000 $, nets
fédéral 71 515 $ et Québec 70 095 $; FSS 18,70 $; impôt total 14 879,56 $;
retenues 17 700 $; remboursement 2 820,44 $. Avec RPA 3 000 $, REER 5 000 $
et cotisations syndicales 600 $, nets 62 915 $ / 62 095 $, FSS inchangé.

Cas invalidité sans salaire ni RL-2 reçu : 20 000 $ à 11400 et 119, dont
20 000 $ à 11410 sans ajout; retenue fédérale 1 800 $, FSS 18,70 $;
impôt total 687,44 $ et remboursement 1 112,56 $, sans crédit handicap.

91 nouveaux cas ciblés passent : 80 de règles/extraction/intégration/stockage/
trace/PDF et 11 GUI. Inspection visuelle à 600 × 400 et 1 000 × 700, haut et bas
du formulaire; actions testées à trois facteurs Tk. Deux rapports fictifs
de deux pages sont rendus avec PyMuPDF et inspectés. Les captures et PDF de
vérification restent dans `tmp/`, exclus de Git. Limites d'OCR, DPI réels,
thèmes, multi-écrans et avertissements existants maintenues.

Validation finale locale : **1 882 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation, en 51,97 s (`python -m pytest -q`, Python
de `.venv`). Aucun test existant n'a été retiré ou désactivé. Une correction
d'extraction conserve le signe des montants RL-2 négatifs pour permettre leur
refus par la validation, avec trois cas de régression. Deux dossiers temporaires
créés dans le bac à sable ont dû être nettoyés après un refus d'accès pendant
la collecte globale; la commande complète finale passe sans exclusion.

Le Bloc 2C a été validé; le Bloc 2D ci-dessous a ensuite été autorisé.

## Bloc 2D — PSV et suppléments 2025

### Sources officielles vérifiées le 16 septembre 2026

Les références ci-dessous visent la déclaration **2025**, indépendamment de
la période ultérieure pendant laquelle la récupération est retenue à la source.

- [ARC — T4A(OAS), cases 18 à 23](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/tax-slips/understand-your-tax-slips/t4-slips/t4a-oas-statement-old-security.html) : 18 pension imposable, 19 brute informative, 20 trop-payé récupéré, 21 suppléments nets (SRG, allocation, allocation au survivant), 22 retenue fédérale, 23 retenue Québec.
- [ARC — pension 11300](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-11300-old-security-pension-oas.html) et [feuille fédérale 2025, page 2, 23500](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf) : seuil 93 454 $, taux 15 %, plafond pension **plus suppléments**, ajustements particuliers et report 42200.
- [ARC — déduction 25000](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-25000-other-payments-deduction.html) : la récupération dépassant la pension et le remboursement AE réduit la déduction des suppléments déclarés à 14600.
- Revenu Québec : [114 — PSV](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/96-a-164-revenu-total/ligne-114/), [148 — suppléments](https://www.revenuquebec.ca/en/citizens/income-tax-return/completing-your-income-tax-return/how-to-complete-your-income-tax-return/line-by-line-help/96-to-164-total-income/line-148/), [295 — déduction des suppléments](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/276-a-298-2-revenu-imposable/ligne-295/), [250 point 3 — report de 23500](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-250/point-3/), [451 — retenues](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/451-a-480-remboursement-ou-solde-a-payer/ligne-451/).
- [Revenu Québec — annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : lignes 22 et 29 retirent respectivement la PSV 114 et les suppléments 148 de l'assiette FSS. Les salaires sont également exclus : FSS nul dans le profil PSV pris en charge.

### Calcul et correspondances

| T4A(OAS) / calcul | Fédéral | Québec |
| --- | --- | --- |
| Case 18 | Pension 11300 | Pension 114 |
| Case 19 | Information, jamais additionnée à 18 | Même règle |
| Case 20 non nulle | Refus explicite du remboursement complexe | Refus explicite |
| Case 21 | Suppléments 14600, inclus dans le revenu net | Suppléments 148, code 07 à 149 |
| Suppléments non récupérés | Déduction du revenu imposable 25000 | Déduction du revenu imposable 295 |
| Récupération calculée | Déduction du revenu net 23500; ajout à payer 42200 | Déduction 250 point 3 |
| Case 22 | Retenue 43700, y compris récupération retenue à la source | Aucun deuxième report |
| Case 23 | Aucun ajout à 43700 pour ce résident Québec | Retenue 451 |

Après inclusion de 18 et 21 dans les revenus totaux, les déductions ordinaires
RPA, REER et cotisations syndicales sont appliquées. Dans le profil simple,
le revenu fédéral obtenu est 23400, sans ajustements AE/PUGE/REEI.
La récupération est `min(18 + 21, 15 % × max(0, 23400 - 93454))`, arrondie au
cent. Elle diminue les revenus nets et imposables fédéral et Québec, puis
s'ajoute au rapprochement fédéral **après** l'abattement Québec. La retenue
22 n'est ni un revenu négatif ni la récupération annuelle calculée.

La part des suppléments récupérés est `max(0, récupération - pension)`.
La déduction 25000/295 est `max(0, suppléments - suppléments récupérés)`.
Elle réduit uniquement les revenus imposables : le revenu net utilisé pour
les crédits conserve les suppléments, après la récupération. Aucun crédit
pour revenu de pension 31400/361 n'est créé par la PSV. Les crédits d'âge
restent soumis à leur profil validé et au revenu net calculé.

### Périmètre, confirmation et refus

Un seul T4A(OAS), avec ou sans le profil salarial T4/RL-1 ordinaire, pour un
bénéficiaire résident Canada/Québec toute l'année. Aucun feuillet salarial
fictif sans emploi. PSV seule, PSV avec suppléments et suppléments seuls
sont admis; dans ce dernier cas, la case 18 doit être validée à zéro.
La case 18 est obligatoire; 19, 20, 21, 22 et 23 sont facultatives après
revue du feuillet complet. Si 19 est présente, elle doit égaler 18 puisque
le remboursement 20 est exclu. Chaque montant doit être fini, non négatif,
au cent près, et au plus 999 999 999,99 $. Doublons, plusieurs T4A(OAS),
sources absentes et statuts non validés sont refusés.

La confirmation `psv_confirme` est un booléen strict et couvre bénéficiaire,
année, résidence, complétude et absence des cas exclus. Refus explicites :
case 20 non nulle, autres cases non nulles, montants négatifs (y compris 21),
combinaison avec AE/RQAP/RRQ-RPC ou autres revenus non intégrés, confirmations
concurrentes, crédit de pension demandé et RAMQ publique avec suppléments.
Le guide ARC prévoit zéro à 14600 pour un 21 négatif; ce remboursement
reste volontairement exclu plutôt que normalisé silencieusement ici.

Paiements rétroactifs, décès du déclarant, non-résidence, exonérations,
remboursements, fractionnement, ajustements PUGE/REEI et cotisations RRQ
salariales particulières sont hors périmètre. L'allocation ordinaire au
survivant en case 21 n'est pas une déclaration de personne décédée.
Les situations non identifiables par les cases exigent la revue humaine;
la confirmation ne prétend pas les détecter automatiquement. Les exemptions
RAMQ liées aux suppléments ne sont pas calculées; un profil RAMQ vide reste
une estimation préliminaire sans prime, selon le fonctionnement existant.
Les limites existantes sur 34990 et les hauts revenus sont conservées.

### Parcours et vérification

Classification T4A(OAS) distincte de T4A(P); extraction signée des six cases,
validation comptable, confirmation défilante, calcul, sauvegarde/rechargement,
résumé, trace et PDF intégrés. Un feuillet reconnu sans case ne peut pas être
omis à la préparation. Toute nouvelle extraction retire la confirmation;
une nouvelle confirmation invalide le résultat et le PDF précédents. Les
anciens JSON sans ce champ se chargent avec confirmation fausse.

Exemple salarié fictif : salaire 52 000 $, PSV 10 000 $, suppléments 2 000 $.
Revenus totaux 64 000 $; nets fédéral 63 515 $ / Québec 62 095 $;
imposables 61 515 $ / 60 095 $. Récupération et FSS nuls. Retenues PSV
1 500 $ / 500 $, ajoutées une fois aux retenues salariales.
Avec RPA 3 000 $, REER 5 000 $ et cotisations syndicales 600 $, nets
54 915 $ / 54 095 $, imposables 52 915 $ / 52 095 $.

Exemple sans emploi : pension 10 000 $, suppléments 12 000 $, revenus nets
22 000 $ dans les deux juridictions et revenus imposables 10 000 $.
Exemple de feuille de récupération : 23400 = 100 000 $, pension 10 000 $,
suppléments 2 000 $ donne récupération 981,90 $ et déduction 2 000 $.
Avec 23400 = 166 787,33 $, récupération 11 000 $, dont suppléments 1 000 $,
et déduction 25000/295 réduite à 1 000 $. Ces exemples de feuille vérifient
les formules séparément des limites de hauts revenus du moteur global.

Le Bloc 2E a ensuite été autorisé; voir ci-dessous.

Vérification visuelle locale : formulaire inspecté à 600 × 400 et
1 000 × 700, en haut et en bas; actions également testées à trois facteurs
Tk (96/72, 144/72, 192/72). Deux PDF fictifs de deux pages, salarié et sans
emploi, ont été rendus avec PyMuPDF et inspectés intégralement. Aucune coupe
ou superposition relevée. Les captures et rapports restent dans `tmp/`,
exclus du commit. Les limites d'OCR, de DPI réels, de thèmes et de
multi-écrans restent celles de l'application.

Validation finale : **1 963 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation existants, en 60,39 s avec
`python -m pytest -q` (Python de `.venv`). Les 81 nouveaux cas comprennent
71 cas de règles/extraction/intégration/stockage/trace/PDF et 10 cas GUI.
Aucun test existant n'a été retiré ou désactivé. Le cas salaire 90 000 $ et
PSV 8 000 $ confirme 23400 = 96 926 $, récupération 520,80 $, revenu net
fédéral 96 405,20 $ et Québec 94 985,20 $; une déduction REER de 5 000 $
annule cette récupération. L'attente de ce test a été corrigée pour utiliser
la déduction RRQ supplémentaire 2025 de 1 074 $ (678 $ + 396 $).

## Bloc 2E — pensions, FERR et rentes 2025

Parcours intégré : classification, extraction signée, validation des cases,
formulaire défilant, confirmation, estimation, trace, PDF et stockage JSON.
Une seule nature domestique et une paire de feuillets par personne sans
conjoint au 31 décembre, résidente Canada/Québec toute l'année, avec ou sans
le profil salarial ordinaire déjà pris en charge.

| Nature confirmée | Feuillets appariés | Fédéral avant 65 ans | Fédéral dès 65 ans |
| --- | --- | --- | --- |
| RPA viagère | T4A 016 / RL-2 A | 11500, admissible 31400 | 11500, admissible 31400 |
| Rente ordinaire | T4A 024 / RL-2 B | 13000, sans 31400 | 11500, admissible 31400 |
| Variable non viagère | T4A 133 / RL-2 A | 13000, sans 31400 | 11500, admissible 31400 |
| Variable viagère RPA | T4A 133 / RL-2 A | 11500, admissible 31400 | 11500, admissible 31400 |
| RPAC | T4A 194 / RL-2 B | 13000, sans 31400 | 11500, admissible 31400 |
| FERR | T4RIF 16 / RL-2 B | 13000, sans 31400 | 11500, admissible 31400 |
| Pension RPA de fiducie | T3 31 / RL-16 D | 11500, admissible 31400 | 11500, admissible 31400 |
| Rente T5 ordinaire | T5 19 / RL-2 B | 12100, sans 31400 | 11500, admissible 31400 |

Le revenu est ajouté une seule fois. La contrepartie Québec alimente 122 et
l'admissibilité 361, indépendamment des règles fédérales. Les profils de
crédit vides sont alimentés depuis les feuillets; les profils personnalisés
restent soumis aux contrôles de cohérence. Les crédits d'âge ne sont pas
réclamés automatiquement. T3 26 doit égaler 31; T4RIF 24 et RL-2 B-1 sont
des informations sur l'excédent déjà inclus, jamais des revenus additionnels.
Les retenues T4A 022/T4RIF 28 et RL-2 J sont ajoutées une fois. Le FSS 446
utilise la pension brute, sans déduction RPA/REER et sans abattement fédéral.

### Confirmation et persistance

Nature, âge entier de 18 à 120 ans, source de l'âge et confirmation explicite
sont requis. Modifier la nature, l'âge, sa source ou les indicateurs décès/
revenu étranger décoche immédiatement la confirmation. Une extraction ou
une nouvelle préparation invalide le profil; une confirmation appliquée
invalide le calcul et le PDF antérieurs. Le formulaire refuse un dossier
changé depuis son ouverture. Les anciens JSON sans profil pensions se
chargent sans confirmation. Les valeurs JSON mal typées, les confirmations
concurrentes, les sources absentes, les doublons et les feuillets non appariés
sont refusés. Un feuillet reconnu sans case ne peut pas être omis du dossier.

### Vérification et limites

151 tests ciblés couvrent règles, âge, extraction, refus, retenues, FSS,
crédits, stockage, résumé, trace, PDF et parcours GUI. Actions testées à
trois facteurs Tk (96/72, 144/72 et 192/72). Inspection visuelle du formulaire
à 600 × 400 et 1 000 × 700, en haut et en bas; quatre PDF fictifs RPA/FERR/T5/T3,
soit 11 pages rendues avec PyMuPDF et inspectées intégralement, sans coupe
ni superposition. Les captures et rapports restent dans `tmp/`, hors commit.

Limites : une seule paire et une seule nature; aucune combinaison avec PSV,
RRQ/RPC, AE ou RQAP. Décès, revenus étrangers, rétroactivité, fractionnement,
transferts, remboursements, régimes au profit du conjoint, exonérations et
autres revenus hors profil sont exclus. La confirmation humaine reste
nécessaire pour les situations non identifiables par les cases. Les garde-fous
existants (notamment 34990, hauts revenus et RAMQ), ainsi que les limites OCR,
thèmes, DPI réels et multi-écrans, restent applicables.

Les blocs 2F, 2G et 2H ont été autorisés successivement sous condition de
validation complète et de CI verte du bloc précédent. Arrêt après 2H.

Validation finale locale : **2 114 tests réussis**, aucun échec ni test ignoré,
8 avertissements de dépréciation existants, en 61,59 s avec
`python -m pytest -q` (Python de `.venv`, chemins Tcl/Tk explicites).
Le test de refus d'un type non pris en charge utilise désormais T4RSP,
puisque T5 est intégré au Bloc 2E. Aucun test retiré ou désactivé.

## Bloc 2F — retraits REER et sommes forfaitaires 2025

### Audit officiel et décisions

Sources consultées le 20 septembre 2026, pour l'imposition 2025 :

- [ARC, tableau des revenus de retraite 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/5000-g.html).
- [ARC, cases T4RSP et déclaration des revenus](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/completing-slips-summaries/t4rsp-t4rif-information-returns/t4rsp-slip-summary/t4rsp-statement-rrsp-income.html).
- [ARC, guide T4040 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4040/rrsps-other-registered-plans-retirement.html).
- [ARC, T4 et allocations 66/67](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120/employers-guide-filing-t4-slip-summary.html).
- [Revenu Québec, guide TP-1.G 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf), lignes 122, 154 et 250.
- [Revenu Québec, guide RL-2](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/rl-2-g/guide-du-releve-2-revenus-de-retraite-et-rentes/), nature de la case C, remboursement F et retenue J.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) et [annexe B 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.B%282025-12%29.pdf).

| Cas audité | Fédéral | Québec | Décision logicielle |
| --- | --- | --- | --- |
| Retrait ordinaire REER non échu, T4RSP 22 | 12900 | RL-2 C, 154 point 6 | Intégré, sans transfert ni remboursement de cotisations |
| Cotisations inutilisées, T4RSP 20 | 12900 et déduction 23200 | RL-2 F, 154 point 4 et 250 point 6 | Intégré avec T3012A approuvé et droit intégral confirmé |
| Forfait RPA domestique T4A 018 | 13000 | RL-2 C, 154 point 6 | Intégré, sans antériorité 1972, transfert ou code spécial |
| Rente périodique T4RSP 16 | 12900; crédit selon âge/nature | 122 selon nature | Exclue de ce parcours, ne pas traiter comme retrait |
| Remboursement de primes T4RSP 18; décès 34 | 12900, règles successorales | D/E et autres cases selon bénéficiaire | Exclus : décès/conjoint et roulements non intégrés |
| Désenregistrement T4RSP 26 | 12900 | Traitement selon nature | Exclu : ce n'est pas un retrait ordinaire |
| T4RSP 28 positif/négatif | 12900 ou déduction 23200 | H/154 ou I/250 point 5 selon nature | Exclu : preuve et historique nécessaires |
| T4A 106 | 13000, exonération décès éventuelle | Prestation de décès selon source | Exclu |
| T4 66/67 | 13000, distinct de 14 | Allocation de retraite, RL-1 O/154 | Détecté et refusé : transferts et appariement non intégrés |
| T4RSP 25/27, 24/36, 35/37/40 | RAP/REEP, conjoint, transfert ou succession | L/O, attribution et autres cases | Exclus explicitement |

La case B du RL-2 n'est pas utilisée par défaut pour un retrait non échu.
Les forfaits retenus n'alimentent pas 122 ni les crédits 31400/361. Les
retenues T4RSP 30 ou T4A 022 et RL-2 J sont ajoutées une fois; aucun cumul
du revenu fédéral et de sa contrepartie Québec. Le FSS utilise le forfait
brut, diminué de la déduction 250 point 6 dans le seul parcours remboursé.

### Chaîne et limites

Extraction signée des cases T4RSP (y compris celles refusées), T4 66/67 et
T4A 018/106/108, validation humaine, formulaire, calcul, stockage JSON,
résumé, trace et PDF intégrés. Une seule paire de feuillets; avec ou sans
emploi ordinaire. Nature/source modifiées : confirmation retirée. Extraction,
préparation ou validation appliquée : estimation et lien PDF invalidés.
Ancien JSON sans profil : confirmation fausse. Types JSON, montants,
doublons, provenance, appariement et confirmations concurrentes contrôlés.

RAP/REEP, décès, conjoint, transferts, rétroactivité, revenus étrangers,
plusieurs natures et combinaisons avec pensions/PSV/RRQ/AE/RQAP restent
exclus. Un négatif 28 n'est jamais normalisé en retrait ou ignoré.
L'extraction des marqueurs ne remplace pas la revue complète, notamment
pour les indicateurs textuels 24 et la nature du régime. Les garde-fous
34990, RAMQ, hauts revenus et cotisations salariales sont conservés.

Validation 2F : **95 nouveaux tests** (87 moteur/stockage/trace/PDF et 8 GUI),
**2 209 tests réussis** dans la suite complète, 8 avertissements existants,
aucun test ignoré. Inspection GUI à 600 × 400 et 1 000 × 700 et des six pages
de trois PDF. Bibliothèques Tcl/Tk copiées localement dans `tmp/` pour le
dernier lancement Windows (63,76 s); l'intermittence du chargement système
reste une limite d'environnement. Aucun fichier temporaire inclus dans Git.

## Bloc 2G — fractionnement du revenu de pension 2025

Audit officiel 2025 : [T1032 ARC](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t1032/t1032-25e.pdf),
[annexe Q](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.Q%282025-12%29.pdf),
[annexe B](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.B%282025-12%29.pdf)
et [annexe F](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf).
Le choix fédéral (21000/11600) et le choix Québec (245/123) sont indépendants,
plafonnés chacun à 50 % de la pension admissible. Le Québec exige un cédant
de 65 ans; la rente viagère RPA fédérale est admissible avant cet âge.
Les retenues admissibles sont réparties proportionnellement, avec un seul
arrondi du transfert : soustraction au cédant, addition au bénéficiaire.
Les retenues Québec sont exclues de la retenue fédérale. Les deux revenus
nets et les retenues totales sont conservés; les revenus totaux avant
déduction ne doivent pas être confondus avec les revenus nets.

Parcours local de couple distinct, indivisible : deux T4A 016/RL-2 A appariés,
retenues T4A 022/RL-2 J exclusivement relatives à ces pensions, sources et
âges revus manuellement. L'extraction existante des feuillets demeure
disponible, mais l'importation automatique de deux dossiers individuels
n'est pas intégrée. Le choix est saisi après validation des pièces, sans
optimisation ni production des formulaires officiels signés. Le calcul
revoit 30100, 31400, l'annexe B commune (une réduction familiale, répartition
361 explicite), les impôts et le FSS après transfert.

Limites logicielles explicites : seules les rentes viagères RPA; résidence
Canada/Québec et union toute l'année, assurance médicaments privée complète.
Nets de chaque conjoint compris entre 30 000 et 57 375 $ dans les deux
juridictions, pour exclure les crédits conjugaux inutilisés et préserver
le garde-fou 34990. Aucun salaire, autre revenu, PSV/RRQ/AE/RQAP, FERR,
déduction, crédit particulier, succession, changement conjugal ou transfert
de crédits. Ces bornes ne constituent pas des conditions légales générales.

JSON de couple séparé avec schéma strict et écriture atomique; brouillons
autorisés, calcul interdit sans les trois confirmations. Les anciens JSON
individuels restent compatibles avec leur parcours, sans conversion implicite.
Toute modification révoque les confirmations et le résultat/PDF; le
rechargement rétablit les données validées mais impose un nouveau calcul.
Résumé, trace des deux déclarations et PDF conjoint sont intégrés.

Validation ciblée : 57 nouveaux tests, dont conservation et arrondis,
conditions d'âge, choix indépendants, refus de profils incohérents,
persistance, confirmations, PDF périmé et GUI à trois facteurs Tk.
Inspection visuelle à 600 × 400 et 1 000 × 700 (haut, milieu, bas) et des
deux pages du PDF fictif. Captures et rapports exclusivement dans `tmp/`.

Suite complète 2G : **2 266 tests réussis**, aucun test retiré, désactivé ou
ignoré; 8 avertissements existants, 63,90 s avec le Python `.venv` et les
bibliothèques Tcl/Tk locales. Les profils individuels précédents restent testés.

## Bloc 2H — autres prestations de remplacement 2025

### Audit et périmètre retenu

Sources officielles pour 2025, consultées le 20 septembre 2026 :

- [ARC, indemnités pour accidents du travail, 14400](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-144-workers-compensation-benefits.html).
- [ARC, assistance sociale, 14500](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/revenu-personnel/ligne-145-prestations-assistance-sociale.html).
- [ARC, déduction 25000](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-25000-other-payments-deduction.html).
- [ARC, feuillet T5007 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/t5007.html).
- [ARC, guide fédéral 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/5000-g.html), étape 2, lien vers les [sommes non déclarables](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/amounts-that-taxed.html) : indemnité provinciale à une victime d'accident automobile.
- [Revenu Québec, guide TP-1.G 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf), lignes 147, 148, 295 et 358.
- [Déclaration TP-1 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D%282025-12%29.pdf), [annexe F](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) et [annexe E](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.E%282025-12%29.pdf).

| Profil intégré | Fédéral | Québec |
| --- | --- | --- |
| Assistance sociale ordinaire, T5007 11 = RL-5 A | 14500; déduction 25000 | 147; aucune déduction 295 |
| CNESST courante, T5007 10 = RL-5 C | 14400; déduction 25000 | 148, source 01; déduction 295; M vers 358 |
| SAAQ courante, victime de l'accident, RL-5 D seul | Aucun revenu ni déduction 25000 | 148, source 03; déduction 295; M vers 358 |

25000 et 295 réduisent le revenu imposable, pas le revenu net utilisé pour
les crédits. Les montants fédéral et Québec appariés ne sont jamais
additionnés. Le redressement M est explicitement requis, même nul, et
plafonné à 16 713,90 $; le crédit personnel utilise (18 571 − M) × 14 %.
L'annexe F exclut 147/148 : aucune cotisation FSS sur ces prestations.
L'annexe E n'est pas le calcul de 358; aucun redressement d'impôt
rétroactif 443 n'est simulé.

### Refus et limites

Une seule paire de feuillets distincts (RL-5 seul pour SAAQ), une nature, avec ou sans emploi
ordinaire, résidence Canada/Québec toute l'année et sans conjoint. L'aide
fédérale peut devoir être attribuée au conjoint au revenu net supérieur :
ce parcours conjugal est exclu. Les remboursements à l'employeur exigent
un traitement distinct et sont refusés par confirmation explicite.

SAAQ : le revenu net fédéral demeure inchangé, tandis que le revenu net
Québec augmente. Un T5007 concomitant est refusé; aucune assimilation à
CNESST. Le décès et la compensation pour perte d'un soutien financier
restent exclus. Sont aussi refusés B/K, E (retrait préventif et autres indemnités),
H/P (remboursements), O (années antérieures), revenu de base Q, régimes
hors Québec nécessitant TP-752.0.0.6, décès, revenus étrangers, cas mixtes,
autres prestations de retraite/remplacement et RAMQ publique. Les codes
textuels doivent être revus sur la pièce : l'extraction numérique ne prouve
pas leur absence. Aucune règle inventée pour une prestation non couverte.
Les limites préexistantes sur crédits remboursables, 34990 et OCR demeurent.

### Chaîne et validation

Classification T5007/RL-5, extraction signée des cases, validation de la
provenance, refus des doublons et des paires discordantes, calcul,
formulaire défilant, résumé, trace, PDF et JSON intégrés au dossier fiscal.
Les anciens JSON sans profil reçoivent un profil non confirmé. Nature ou
source modifiée : confirmation retirée; extraction/préparation/application :
estimation et ancien PDF invalidés. Rechargement testé avec nouveau calcul.

89 nouveaux tests ciblés : 81 moteur/extraction/stockage/trace/PDF et 8 GUI.
Inspection visuelle des six vues GUI à 600 × 400 et 1 000 × 700 et des six
pages de trois PDF fictifs avec emploi. Aucun débordement de texte constaté.
Captures et PDF conservés exclusivement dans `tmp/`, hors Git.

Arrêt après ce bloc. La Priorité 3 n'est pas commencée.

Validation finale 2H : **2 355 tests réussis**, 8 avertissements existants,
aucun échec ni test ignoré, en 69,19 s (`python -m pytest -q`, Python `.venv`,
Tcl/Tk local). Aucun test antérieur retiré ou désactivé.

### Bilan des validations de la Priorité 2

| Bloc | Nouveaux tests | Total à la clôture | Commit |
| --- | ---: | ---: | --- |
| 2A RQAP | 77 | 1 726 | 3915e8a |
| 2B AE | 65 | 1 791 | 4467004 |
| 2C RRQ/RPC | 91 | 1 882 | c5f8b58 |
| 2D PSV | 81 | 1 963 | 89b83fd |
| 2E Pensions | 151 | 2 114 | 395f228 |
| 2F Retraits | 95 | 2 209 | 81c5f2f |
| 2G Fractionnement | 57 | 2 266 | d344e82 |
| 2H Autres prestations | 89 | 2 355 | Voir le commit de cette section |

706 tests ajoutés depuis les 1 649 tests du socle avant 2A. Les profils
pris en charge sont strictement ceux décrits dans chaque bloc; cette
priorité ne constitue pas une couverture universelle des prestations,
des familles, des cumuls de revenus ni des déclarations de retraite.

## Priorité 3 — audit et découpage des revenus de placement 2025

Audit du 20 septembre 2026, **avant toute modification du code 3A**, sur le
socle 2H `4744592` (2 355 tests). Seul 3A est autorisé à être implémenté
dans cette étape; arrêt après son commit, son push et sa CI pour bilan.

### Références officielles et décisions fiscales

- [ARC, feuille de calcul fédérale 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf) : 12010 est inclus dans 12000; montants imposables des T5 11/25 et T3 32/50, sans ajouter une seconde fois les dividendes réels. Majorations 15 %/38 % selon nature; crédit 40425 distinct des crédits au taux de base. 12100 reçoit notamment T5 13/14/15/30 et T3 25, avec retrait des montants déjà déclarés antérieurement.
- [ARC, intérêts 12100](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-12100-interest-other-investment-income.html) : intérêts payés/crédités et intérêts de remboursement d'impôt déclarables même sans T5 et sous 50 $. CPG composés : année de placement complète, sans attendre l'encaissement. Compte commun : quote-part liée aux apports, pas partage arbitraire. Bons du Trésor vendus avant échéance et billets liés peuvent combiner intérêts et capital.
- [ARC, T5](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/tax-slips/understand-your-tax-slips/t5-slips/t5-statement-investment-income-slip-information-individuals.html) : 13 intérêts canadiens; 10/11/12 dividendes autres que déterminés; 24/25/26 déterminés; 18 gains en capital; 15/16 revenu/impôt étranger; 19 rentes et 30 billets liés à distinguer.
- [ARC, guide T3 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4013/t3-trust-guide.html) : 23/32/39 autres dividendes, 49/50/51 déterminés; 21 gains, 25/34 revenu/impôt étranger non commercial, 42 ajustement du PBR. **26 est composite** (intérêts, location, entreprise, pension, etc.); aucune attribution automatique de toute cette case à 12100. Crédit fédéral des dividendes : 9,0301 %/15,0198 % des montants imposables selon nature.
- [Revenu Québec, RL-3 version 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/rl/RL-3%282025-10%29.pdf) : D → 130; A1/A2 → 166/167, B → 128, C → 415; F/G revenu/impôt étranger; I gains; J rentes; K billets liés. Une devise et les comptes communs nécessitent un traitement distinct.
- [Revenu Québec, guide TP-1.G 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf) : intérêts 130, dividendes 128 avec renseignements 166/167, crédit 415 (RL-3 C, RL-16 J). Sans relevé, crédit = 16,1460 % du dividende déterminé réel + 3,9330 % de l'ordinaire réel. Frais 231, rajustements 260/276; pertes antérieures 290 avec TP-729. Crédit étranger 409 via TP-772/annexe E; impôt non commercial disponible réduit du crédit fédéral. T3/RL-16 et T5008/RL-18 décrivent les mêmes opérations : ne jamais additionner les contreparties.
- [ARC, gains en capital 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4037/capital-gains.html) et [annexe G Québec 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.G%282025-12%29.pdf) : produit moins PBR et frais d'aliénation; inclusion ordinaire **50 % en 2025**, fédéral 12700/annexe 3, Québec 139. Une perte nette ne réduit pas le salaire; report rétrospectif de trois ans ou prospectif sans limite dans le cas ordinaire. Pertes apparentes, biens personnels/précieux, entreprise, réserves, décès et exonérations exigent des règles propres. Ne pas coder une proposition de taux aux deux tiers comme règle 2025.
- [ARC, T5008](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/tax-slips/understand-your-tax-slips/t5-slips/t5008-statement-securities-transactions-slip-information-individuals.html) : case 21 produit; case 20 coût comptable **pas nécessairement le PBR**. Registre des lots/coût moyen, frais, devise et distributions nécessaires; pas de calcul aveugle 21 − 20.
- [ARC, pertes antérieures 25300](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-25300-pertes-capital-nettes-autres-annees.html) : soldes non utilisés, ordre des années et ajustement au taux d'inclusion applicables. Distinguer revenu net et imposable; ne pas consommer un report deux fois. Reports fédéraux et Québec conservés séparément.
- [ARC, frais 22100](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-22100-carrying-charges-interest-expenses.html) : frais admissibles et emprunts utilisés pour produire un revenu, exclusions pour régimes enregistrés et frais de transaction à traiter dans le PBR/produit. [Annexe N Québec 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.N%282025-12%29.pdf) : excédent des frais sur revenus à 260; interaction des pertes 290 à 276; solde et utilisation 252 à suivre séparément. Pas de simple copie de 22100 vers une déduction Québec nette.
- [ARC, crédit étranger 40500 pour 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-40500-federal-foreign-tax-credit.html) : T2209, revenus bruts et impôts convertis en CAD, ventilation par pays/nature et limites conventionnelles; revenu exonéré par convention exclu du calcul. Les retenues étrangères ne sont pas des retenues canadiennes 43700/451. Dividendes étrangers sans crédit canadien pour dividendes; T1135 et TP-1079.8.BE à examiner séparément.
- [Annexe F Québec 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : intérêts 130 dans l'assiette FSS; salaire exclu, déductions admises propres à l'annexe. Seuil 18 130 $, 1 % plafonné à 150 $ jusqu'à 63 060 $, puis 150 $ + 1 % de l'excédent, maximum 1 000 $. Ne pas calculer et additionner un plafond par feuillet.

### Sous-blocs proposés et dépendances

| Bloc | Périmètre à construire | Dépendances et garde-fous |
| --- | --- | --- |
| **3A — intérêts canadiens sur feuillets** | Une paire T5 13/RL-3 D, CAD, titulaire unique; 12100/130 et FSS | Extraction, validation des pièces et du profil, GUI, JSON, résumé, trace, PDF; implémenté |
| 3B — intérêts sans feuillet et autres intérêts documentés | Relevés bancaires, impôt remboursé, CPG courus; T3/RL-16 après ventilation | Identifiants des sources, déduplication avec 3A, échéanciers, intérêts déjà déclarés; attribution et devises restent exclus jusqu'à couverture |
| 3C — dividendes canadiens | Déterminés/autres; T5/RL-3 puis T3/RL-16; majorations, crédits fédéral/Québec | Ordre des crédits et abattement, revenu net majoré, FSS, refus TOSI/cas particuliers; conservation des revenus réels et imposables |
| 3D — dispositions et distributions en capital | Annexe 3/G, T5008/RL-18, T3/RL-16 et T5/RL-3 | PBR prouvé, frais, historique, pertes apparentes, taux 2025; différencier revenu d'entreprise et capital, contrôler impôt minimum |
| 3E — frais de placement et annexe N | 22100/231, 260/276, reports 252 | Utilisation des emprunts, frais admissibles, revenus de placement des blocs précédents, soldes distincts; aucune double déduction de frais de transaction |
| 3F — reports de pertes en capital | 25300/290, T1A/TP-1012.A, TP-729, soldes historiques | 3D et 3E; taux d'origine, avis de cotisation, ordre d'utilisation, plafonds et non-double consommation |
| 3G — placements et impôts étrangers | Revenus bruts/devises, T2209/40500, TP-772/409, déclarations de biens étrangers | Pays, convention, limites de crédit et déductions connexes; pas de conversion ou crédit implicites |
| 3H — combinaisons contrôlées | 3H-A livré : intérêts + dividendes; 3H-B livré : intérêts + dividendes + frais; 3H-C livré : intérêts + dividendes + capital; 3H-D livré : intérêts + dividendes + capital + frais; 3H-E livré : intérêts + dividendes + capital + reports de pertes; 3H-F livré : intérêts + dividendes + capital + frais + reports de pertes | Assiette FSS globale recalculée selon la combinaison; déductions/crédits et interactions propres validés avant ouverture |

### Contrat du premier sous-bloc 3A

Intérêts courants de source canadienne uniquement, T5 13 = RL-3 D, une paire
distincte validée et un propriétaire bénéficiaire unique, comptes non
enregistrés en CAD. Aucun ajout manuel d'intérêts sans feuillet. Les montants
augmentent revenu total, net et imposable dans chaque juridiction, une seule
fois; aucune retenue présumée. Avec ou sans un emploi ordinaire T4/RL-1.

Refus explicite : autres cases monétaires positives, dividendes, T3,
T5008/RL-18, gains/pertes, reports, frais de placement, impôt étranger,
devises, copropriété/attribution, intérêts déjà déclarés, billets liés,
assurance vie, successions et mélanges avec pensions ou prestations.
Les feuillets T5 de rente du Bloc 2E conservent leur parcours : l'identifiant
T5 seul ne suffit pas à sélectionner 3A. Les garde-fous 34990, crédits,
RAMQ, revenus élevés et confidentialité locale demeurent.

Toute modification pertinente doit révoquer la confirmation, invalider
l'estimation et empêcher l'export du PDF antérieur. Ancien JSON sans profil
intérêts : profil non confirmé. Arrêt obligatoire après validation de 3A.

### Réalisation du Bloc 3A

La chaîne locale est intégrée : classification RL-3, extraction des cases,
validation T5 13 / RL-3 D, calcul 12100/130, FSS 446, formulaire défilant,
JSON, résumé, trace et PDF. Les pièces sans données validées, cases
dupliquées, sources absentes, montants négatifs/non finis et divergences
d'appariement sont refusés. Les profils des autres prestations ne se
cumulent pas avec 3A. Une correction des données révoque la confirmation;
une nouvelle application du profil invalide l'estimation et son ancien PDF.

Le [T5 officiel 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t5/t5-25e.pdf)
confirme que la case 23 est un **code**, pas un revenu : seul 1 est accepté
si cette case est saisie. Le code 2 (compte conjoint) est refusé. Les cases
21, 22, 27, 28 et 29 ne sont pas extraites comme des montants; identité,
devise, validité du feuillet et absence de doublons sont vérifiées et
confirmées humainement sur les pièces complètes. L'extraction reste une
aide soumise à validation, sans lecture automatique fiable de toute mise
en page bancaire ni des codes textuels. Aucune somme de plusieurs paires.

Le FSS utilise les intérêts bruts admissibles : seuil 18 130 $, premier
plafond 150 $, reprise au-delà de 63 060 $, plafond final 1 000 $.
Le salaire et la déduction REER ordinaire ne changent pas cette assiette.
Le refus historique au-delà de 129 590 $ lié aux crédits pour dons a été
levé par 5J. Le calcul intégré des intérêts et du FSS est maintenant testé
à haut revenu; les autres exclusions du profil restent distinctes.

Exemples synthétiques vérifiés : 20 000 $ d'intérêts sans emploi donnent
561,29 $ d'impôt fédéral de base, 468,68 $ après abattement Québec,
200,06 $ d'impôt Québec et 18,70 $ de FSS, soit 687,44 $ au total.
Avec le dossier salarial synthétique de 52 000 $, les revenus nets sont
71 515 $ au fédéral et 70 095 $ au Québec; les retenues restent 13 700 $.

Validation 3A : 106 nouveaux tests ciblés (99 moteur/persistance/PDF et
7 GUI). Inspection visuelle du formulaire à 600×400 et 1000×700, tests
d'accès aux boutons à 96/144/192 DPI, et inspection de toutes les pages
des trois PDF synthétiques (sans emploi, avec emploi, second palier FSS).
Les artefacts de contrôle restent dans `tmp/`, exclus de Git.

Suite complète finale : **2 461 tests réussis**, 8 avertissements de
dépréciation existants, aucun test retiré ou désactivé. Le code bénéficiaire
T5 23 est aussi distingué des revenus dans le parcours rente 2E; les
scénarios avant/après 65 ans restent identiques et le code conjoint reste
refusé. Les Blocs 3B à 3G sont maintenant livrés; 3H-A est maintenant livré et les autres combinaisons 3H restent à implémenter.

### Audit préalable du Bloc 3B — intérêts documentés, 2025

Audit effectué avant modification du code 3B, sur le socle `45d5e68`.
Le découpage reste inchangé : les dividendes appartiennent à **3C**.

- [ARC 12100, instructions visant 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-12100-interest-other-investment-income.html) : intérêts bancaires payés/crédités, même sans feuillet et sous 50 $, et intérêts de remboursements d'impôt reçus en 2025. CPG : intérêts de chaque année complète de placement, pas uniquement à l'encaissement. Une période juillet 2024–juin 2025 relève de 2025 au fédéral.
- [Guide Québec TP-1.G 2025, page 24, ligne 130](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf) : intérêts sans feuillet et sur remboursement d'impôt déclarables. Plusieurs méthodes de déclaration des contrats sont possibles; ne pas présumer une période Québec identique à la période fédérale. Le code ci-dessous limite donc les CPG aux intérêts annuels du 1er janvier au 31 décembre 2025, échéancier et méthode d'exercice Québec confirmés, aucun changement de méthode ni montant déjà déclaré. Autres anniversaires, échéance partielle, taux variables et historiques ambigus refusés.
- [T3 officiel 2025, page 2](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t3/t3-25b.pdf) : **26 moins 31 va à 13000**, même si la nature économique est un intérêt. La case 25, étrangère, va à 12100 et reste exclue. [Guide T3 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4013/t3-trust-guide.html) : 26 peut aussi contenir loyers, entreprise, décès ou pensions. Aucune assimilation automatique à des intérêts. 3B exige une ventilation confirmant exclusivement des intérêts canadiens ordinaires, case 31 nulle et toutes autres cases monétaires nulles; T3 26 = RL-16 G, Québec 130 selon le guide TP-1.G. Les fiducies personnelles, successions, fiducies désignées et montants mixtes sont exclus; seul un fonds de placement ordinaire documenté est accepté.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : les intérêts Québec 130 sont assujettis au FSS. Aucun crédit pour dividendes, majoration ni retenue implicite. Les montants entrent une fois dans le revenu total, net et imposable; crédits et RAMQ suivent les revenus recalculés et leurs garde-fous existants.

Périmètre sûr retenu : **une source économique documentée**, avec ou sans
emploi, soit banque, remboursement d'impôt, CPG annuel décrit ci-dessus,
ou paire T3/RL-16 exclusivement intérêts après ventilation. Identifiant
stable, période 2025 et justificatif obligatoires. Les pièces appariées
sont des contreparties, jamais des revenus supplémentaires. Les cumuls
3A+3B, sources multiples, devises, attribution, comptes conjoints, frais,
prêts privés, titres négociés et revenus déjà déclarés sont refusés : la
combinaison de plusieurs sources reste réservée à 3H. Cette restriction
empêche notamment de compter le même intérêt sur un relevé bancaire et
son T5. Pas de calcul de rendement à partir d'un taux supposé.

L'extraction des états sans feuillet vise un état d'intérêts 2025 identifié
et des libellés explicites; elle ne transforme pas un solde bancaire ou
le montant principal d'un remboursement en intérêt. Toute extraction
doit passer par la validation comptable existante.

### Réalisation et validation du Bloc 3B

Le profil intérêts conserve les anciens champs 3A et ajoute nature,
identifiant de source, dates et confirmations de ventilation/échéancier.
Les anciens JSON 3A restent compatibles. Le formulaire 3B, les données
validées, la sauvegarde/relecture, le résumé, la trace et le rapport PDF
utilisent ce même profil. Modifier un champ pertinent révoque la
confirmation; modifier les pièces ou appliquer le profil invalide
l'estimation et bloque l'export de son ancien PDF.

Extraction sans feuillet : document identifié « État/Relevé/Avis intérêts
2025 », libellé explicite suivi de `:` et du montant sur la même ligne.
Libellés couverts : « Intérêts bancaires 2025 », « Intérêts crédités 2025 »,
« Intérêts sur remboursement d'impôt 2025 », « Intérêts courus CPG 2025 ».
Les intérêts déjà déclarés, dividendes, frais de placement et impôts
étrangers repérés sont conservés pour provoquer un refus s'ils sont
positifs. Un solde, un capital, un montant placé sur une autre ligne ou
une autre année n'est jamais assimilé à un intérêt. Cette extraction
limitée n'est pas une reconnaissance universelle des relevés bancaires;
les pièces complètes et les informations non extraites doivent être
vérifiées humainement. Les doublons ne sont pas additionnés implicitement.

Contrôles : **99 nouveaux tests ciblés** (83 métier/extraction/persistance/
PDF, 16 GUI), dont conservation de 3A, T3 13000 distinct de 12100,
appariement 26/G, petits montants, seuils FSS, REER sans réduction du FSS,
crédits à revenu net périmé refusés, périodes CPG, JSON invalide,
confirmations révoquées et anciens PDF bloqués. Aucun test retiré ou
désactivé. Inspection visuelle du formulaire 600×400 et 1000×700 et des
huit pages des quatre PDF synthétiques corrigés; boutons vérifiés aussi
à 96/144/192 DPI. Artefacts synthétiques dans `tmp/`, exclus de Git.

Limites maintenues : une seule source, aucun cumul 3A+3B, aucun calcul
automatique d'un rendement CPG, aucun report d'intérêts déjà déclarés,
aucune ventilation d'une fiducie mixte, aucune devise ni attribution.
Les garde-fous spécialisés du moteur global et de la RAMQ restent distincts.
Le refus historique des dons au-delà de 129 590 $ a été levé par 5J.
Les dividendes et tous les blocs 3C à 3H restent à construire.

Suite complète finale `python -m pytest -q` : **2 560 tests réussis**,
8 avertissements de dépréciation existants, aucun échec (82,03 s en local).

### Bloc 3C — audit préalable et périmètre arrêté

Audit du 20 septembre 2026, exclusivement sur les éditions fiscales 2025 :

- [Feuille fédérale 5000-D1 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf) :
  12000 inclut les deux catégories majorées; 12010 est le sous-total ordinaire,
  jamais un revenu supplémentaire. Majorations 38 % et 15 %. 40425 reprend
  les crédits des feuillets, séparément du revenu.
- [T5 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t5/t5-25e.pdf) :
  admissibles 24/25/26, autres dividendes 10/11/12 (réel/imposable/crédit).
  Contrôle des crédits aux taux de 15,0198 % et 9,0301 % du montant imposable.
- [Déclaration fédérale Québec 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.txt) :
  40425 réduit 42900, après les crédits 35000, avec plancher zéro;
  l'abattement 44000 de 16,5 % porte sur ce 42900 réduit.
- [RL-3 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/rl/RL-3%282025-10%29.pdf) :
  A1 et A2 réels vers 166/167, B imposable vers 128, C crédit vers 415.
- [Guide TP-1 2025, lignes 128 et 415](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf) :
  majorations identiques; contrôle du crédit Québec à 16,1460 % du réel
  déterminé et 3,9330 % du réel ordinaire. Crédit non remboursable.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) :
  lignes 23 à 25 retirent la majoration de l'assiette; FSS sur les dividendes
  réels, salaire exclu. Les crédits dividendes ne réduisent pas le FSS.
- [T3 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t3/t3-25b.pdf) :
  admissibles 49/50/51, ordinaires 23/32/39. Le guide TP-1 rattache RL-16 I
  à 128 et J à 415. Les distributions de fiducie restent refusées dans
  cette livraison : validation détaillée des cases réelles et distributions
  mixtes non achevée (PDF RL-16 2025 inaccessible lors de cet audit).

Périmètre accepté avant codage : une seule paire T5/RL-3 distincte et
complète, un particulier titulaire unique, résident Canada/Québec toute
l'année 2025, dividendes canadiens ordinaires et/ou déterminés uniquement,
avec ou sans emploi ordinaire. Les dix cases monétaires 10/11/12/24/25/26
et A1/A2/B/C sont explicites, même nulles. Concordance exacte au cent
après arrondi; un écart est refusé, jamais corrigé silencieusement.
Les revenus total, net et imposable augmentent du seul montant majoré.
Les crédits sont consommés au plus à hauteur de l'impôt disponible.

Refus : plusieurs paires, T3/RL-16, sans feuillet, étranger/devise,
conjoint/attribution/transfert, TOSI, décès/succession, sociétés ou fiducies,
dividendes en capital, comptes non réclamés, frais, intérêts ou autres
placements combinés, pensions/prestations combinées, ajustements 293/297,
minimum alternatif et autres cas complexes. Vérification humaine des
feuillets complets, codes administratifs, année et identité obligatoire.
Les garde-fous globaux et crédits à revenu net recalculé restent applicables.
Les anciennes sauvegardes conservent un profil dividendes vide par défaut.

Livraison 3C : extraction identifiée des cases réelles/imposables/crédits et
des retenues hors périmètre RL-3 207/208; validation de la paire; calcul,
formulaire défilant, JSON, résumé, trace et PDF intégrés. Toute modification
fiscale invalide l'estimation et son PDF; modifier le justificatif révoque
la confirmation, et une nouvelle extraction révoque le profil confirmé.

Validation finale : **118 nouveaux tests**, dont 7 GUI; **2 678 tests réussis**
avec `python -m pytest -q` (87,06 s), huit avertissements de dépréciation
préexistants. Aucun test supprimé ou désactivé. Inspection visuelle du
formulaire en 600×400 et 1000×700, haut et bas accessibles, actions fixes;
tests de disposition à 96/144/192 DPI. Six pages de PDF inspectées :
admissibles seuls, ordinaires seuls, deux catégories avec salaire.
Tous les artefacts sont synthétiques, locaux et exclus de Git dans `tmp/`.

Limites restantes : T5/RL-3 seulement; pas de T3/RL-16 ni cumul avec
intérêts ou autres prestations; dix cases explicites exigées, aucun écart
d'arrondi accepté automatiquement. Vérification humaine de l'identité,
des codes et des exclusions. Le refus historique des dons au-delà de
129 590 $ a depuis été levé par 5J. Les sections suivantes documentent 3D.

### Bloc 3D — audit préalable, dispositions en capital 2025

Audit du 21 septembre 2026 avant codage. Le découpage place les reports
de pertes en **3F** et les frais de placement courants en **3E** : aucun
report antérieur ni déduction 22100/231 n'est ajouté par 3D.

Sources officielles applicables à 2025 et décisions :

- [Annexe 3 fédérale 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s3/5000-s3-25e.pdf) :
  actions cotées, produit 13199, gain/perte 13200; gain = produit − PBR −
  frais de disposition. Inclusion 50 %, résultat positif vers 12700.
  Une perte nette ne devient pas une déduction du salaire.
- [Guide ARC T4037 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4037/capital-gains.html) :
  acquisition et frais d'achat dans le PBR, coût moyen des biens identiques;
  pertes apparentes lorsque rachat par le contribuable ou un affilié dans
  la période de 30 jours avant/après et détention au trentième jour.
  Les pertes nettes ordinaires peuvent servir sur trois années antérieures
  ou les années futures; leur application reste réservée à 3F.
- [Guide ARC T5008, édition du 31 juillet 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4091/t5008-guide-return-securities-transactions.html) :
  case 20 coût comptable, pas nécessairement PBR fiscal. Case 21 produit
  total, sans déduction de frais. La page du formulaire propose désormais
  une édition 2026 : elle n'est pas utilisée comme règle 2025.
- [Guide RL-18.G 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/rl/RL-18.G%282025-10%29.pdf),
  sections 3.13/3.14 : case 20 à vérifier, case 21 diminuée des frais de
  courtage. Les frais bancaires de disposition se déduisent au calcul du
  gain. Contrôle retenu : T5008 21 − courtage = RL-18 21; gain identique
  au fédéral et au Québec, frais déduits une seule fois. SHS désigne une action.
- [Annexe G 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.G%282025-12%29.pdf) :
  actions à la partie B, ligne 10; inclusion 50 % partie F, positif vers
  139. Distributions T3/T5 vers annexe 3 17600/17400 et RL-16/RL-3 vers
  annexe G nécessitent une ventilation; elles sont explicitement exclues.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) :
  139 reste dans l'assiette FSS; salaire retiré. FSS sur le gain imposable
  positif, pas sur le produit ni le gain brut; perte nette : assiette nulle.
- [T691 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/t691/t691-25e.pdf)
  et [TP-776.42 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/tp/TP-776.42%282025-10%29.pdf) :
  prise en compte du gain non imposable dans le revenu modifié; exemptions
  respectives 177 882 $ et 179 990 $. Le parcours refuse salaire brut maximal
  des deux juridictions + gain positif intégral > 177 882 $, même si des
  déductions permettraient un résultat inférieur. Aucun calcul IMR ni report.

Périmètre conservateur arrêté avant codage : un particulier résident
Canada/Québec toute l'année, une seule vente 2025 en CAD, pleine propriété
d'un lot unique d'actions canadiennes cotées (SHS), acheté depuis 2000,
vendu entièrement, avec ou sans emploi ordinaire. Une paire de fichiers
T5008/RL-18 distincts, une transaction chacun. PBR saisi séparément, preuve
d'acquisition et frais d'achat vérifiés; source PBR et confirmation dédiées.
La case 20, absente ou différente du PBR, n'est jamais copiée au calcul.
Courtage et autres frais de disposition explicitement saisis, même nuls,
avec justificatif. Dates, titre, identité, quantité totale, codes, devise
et exhaustivité des opérations vérifiés humainement sur les documents.

Les revenus total/net/imposable augmentent du seul gain imposable positif;
les crédits dépendant du revenu net doivent être revalidés. Une perte est
affichée et sauvegardée comme résultat 2025 à vérifier, sans report consommé
ni solde de report certifié. Refus des achats dans les 30 jours avant la
vente, de tout rachat/option d'achat affilié dans la fenêtre de perte
apparente, des positions multiples, distributions réinvesties, ajustements
PBR, réorganisations, T3/T5, fonds, étranger, conjoints/attribution, options,
entreprise, crypto, immeubles, décès, dons, réserves, exemptions, pertes
antérieures, autres placements et prestations combinés. Les documents
consolidés mixtes sont refusés, sans extraction automatique des transactions.

Validation finale 3D : 117 nouveaux tests (99 métier et 18 GUI), tous réussis;
suite complète `python -m pytest -q` : 2 795 réussis, 8 avertissements de
dépréciation. Une première exécution a rencontré une erreur d'initialisation
Tk dans le module GUI RRQ/RPC; le contrôle isolé (29 tests) et la relance
complète ont réussi sans retirer ni désactiver de test. Inspection visuelle
du formulaire aux dimensions 600 × 400 et 1 000 × 700, avec défilement et
actions accessibles; six pages PDF contrôlées (gain, perte, gain avec emploi).
Persistance, rechargement, révocation des confirmations et invalidation des
PDF périmés vérifiés. Artefacts synthétiques de contrôle conservés hors Git
dans `tmp/`. Le Bloc 3E n'est pas commencé.

### Bloc 3E — audit préalable et contrat accepté (21 septembre 2026)

Le périmètre du tableau reste frais de placement et annexe N, et non les
pertes en capital reportées (3F). Sources officielles 2025 consultées avant
modification du code :

- [ARC, ligne 22100](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-22100-carrying-charges-interest-expenses.html), page portant explicitement sur 2025 : gestion/garde de placements non enregistrés et intérêts payés pour produire intérêts/dividendes; commissions exclues. Un placement ne pouvant produire que des gains ne justifie pas la déduction des intérêts.
- [RQ, guide TP-1.G 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.G%282025-12%29.pdf), lignes 231/252/260/276 : frais admissibles, plafonnement québécois et suivi des reports. [Ligne 231](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-231/) : commissions d'achat au coût, commissions de vente à l'annexe G; emprunts après disposition soumis à règles particulières.
- [Annexe N 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.N%282025-12%29.pdf) : frais 231 à N12/N18; revenus 128/130/139 à N20/N22/N34. N40 = max(0, N18 − N36) vers 260. Partie C/276 liée notamment à 290, donc refusée ici. N70 : ancien solde québécois inutilisé; N78 : demande 252 limitée au solde et au surplus des revenus sur les frais. N80 = N70 + N40 − N78 dans le périmètre accepté.
- [RQ, ligne 252 pour 2025](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/201-a-260-revenu-net/ligne-252/) : somme des rajustements depuis 2004, moins toute utilisation antérieure, y compris rétrospective. Aucun report fédéral équivalent à présumer.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : F56 déduit 231; 252 et 260 ne sont pas des ajustements de cette assiette. Dividendes réels, intérêts bruts ou gain imposable, moins frais 231; un seul FSS recalculé.

Contrat conservateur : un seul parcours de revenus déjà validé 3A, 3B,
3C ou 3D, avec ou sans emploi ordinaire. Titulaire unique, CAD, comptes
non enregistrés; gestion/garde et intérêts simples payés en 2025, montants
identiques admissibles dans les deux juridictions. Factures, preuve du
paiement, contrat et traçabilité directe de l'emprunt vers le placement
déclaré requis; aucune affectation personnelle, mixte, refinancée ou après
vente. Intérêts sur emprunt refusés dans les parcours vente 3D et remboursement
d'impôt 3B. Les honoraires de conseil, frais juridiques/comptables, montants
RL-1 L-4, frais intégrés à un fonds/T3, assurance vie, régimes enregistrés,
frais de transaction, étranger, conjoint, abris fiscaux et cas complexes
restent refusés. Les preuves sont référencées dans le profil; import local
facultatif d'une pièce pour proposer ses montants explicitement libellés,
jamais pour décider automatiquement de leur admissibilité. Pas de somme
automatique de documents ni d'ajout des frais aux feuillets de revenu.

Report 252 : saisie explicite du seul solde Québec vérifié sur les annexes N,
avis et registre de toutes les utilisations depuis 2004; confirmation dédiée.
Demande explicite, sans optimisation ni report rétrospectif automatique.
Solde d'ouverture immuable, consommation 2025 calculée une fois et solde de
clôture séparé; aucun solde fédéral ni perte en capital réutilisé.

22100 diminue les revenus net/imposable fédéraux; 231 − 260 + 252 diminue
les revenus net/imposable Québec. Le revenu total et les retenues restent
inchangés. Les crédits sont recalculés/leurs données de revenu revalidées;
le crédit de dividendes reste indépendant. Refus d'un revenu net négatif
ou d'un déficit nécessitant un report non couvert. Garde-fou IMR : revenu
total avant déductions augmenté de la moitié non imposable du gain positif
au plus 177 882 $, et aucun IMR antérieur. Garde-fous historiques conservés.
Toute modification révoque la confirmation des frais et du report et rend
l'estimation/PDF périmé après application; tout changement du dossier ou
du profil de placement révoque la confirmation 3E. Arrêt après 3E.

Précisions de livraison : les frais courants liés à un remboursement d'impôt
sont refusés (gestion comprise); seul un report 252 documenté est accepté
dans ce parcours. Les revenus des T5/RL-3, intérêts sans feuillet/CPG et
T3/RL-16 déjà ventilés, dividendes T5/RL-3 ou vente T5008/RL-18 restent
validés par leurs consolidateurs existants. Les anciens indicateurs de frais
non traités des profils 3A/3C continuent à bloquer : le montant admissible
doit passer exclusivement par le profil distinct 3E.

L'import local du formulaire propose uniquement les libellés explicites
« Frais de gestion/garde : montant » et « Intérêts payés/sur emprunt : montant »,
sur une pièce portant l'année 2025. Une case vide ne capture pas la ligne
suivante; doublons et montants ambigus sont refusés. Un nouvel import remplace
les propositions, sans cumul. Autres mises en page : transcription vérifiée
requise. L'import n'infère ni admissibilité ni montant de report.

La confirmation est liée par une empreinte locale aux frais, justificatifs,
valeurs du dossier et profils de placement. Toute différence dans un JSON
confirmé impose une revalidation; ce contrôle de cohérence n'est pas une
signature de sécurité. Les anciens JSON sans profil 3E restent lisibles.
Le solde d'ouverture et la demande restent immuables; recalculer/recharger
ne consomme jamais une deuxième fois le report. Le FSS final remplace celui
du parcours de revenus dans le rapprochement, le résumé, la trace et le PDF.

Validation finale 3E : **129 nouveaux tests** (113 métier, 16 GUI), tous
réussis; contrôle étendu avec les tests de mise en page : 157 réussis.
Suite complète `python -m pytest -q` : **2 924 réussis**, 8 avertissements
de dépréciation, 93,54 s. La première exécution avait rencontré une erreur
Tcl `tcl_findLibrary` à la création d'une racine Tk; les contrôles isolés et
la suite complète ont réussi avec les bibliothèques Tcl/Tk de l'installation
Python, sans retirer ni désactiver de test.

Inspection visuelle : formulaire 600 × 400 et 1 000 × 700, trois positions
de défilement; six pages PDF (report 252, excédent des frais avec salaire,
dividendes avec frais). Aucun chevauchement ni bouton inaccessible constaté.
Artefacts synthétiques de contrôle hors Git dans `tmp/`; aucune donnée client
ajoutée. Le Bloc 3F n'est pas commencé.

### Bloc 3F — audit préalable et périmètre retenu

Audit avant code sur le socle 3E `99de3b4` (2 924 tests). Sources officielles
applicables à la déclaration **2025** :

- [ARC, ligne 25300, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-25300-net-capital-losses-other-years.html) : solde inutilisé, pertes les plus anciennes d'abord, plafond des gains imposables; exceptions avant le 23 mai 1985 exclues.
- [ARC, T4037 Gains en capital 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4037/capital-gains.html) : inclusion 50 % de 2001 à 2025; autre taux historique à rajuster. 25300 réduit l'imposable, pas le net. Perte nette 2025 reportable sur gains de 2022–2024 via T1A ou années futures sans limite ordinaire; pas de déduction sur salaire.
- [RQ, ligne 290](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/276-a-298-2-revenu-imposable/ligne-290/) et [TP-729](https://www.revenuquebec.ca/documents/fr/formulaires/tp/TP-729%282024-10%29.pdf) : demande au plus petit du solde et de 139; ordre chronologique; solde au taux de l'année du report. TP-729 version 2024-10 est le formulaire actuellement lié par l'aide 2025, non une règle de calcul de 2024 appliquée aveuglément.
- [RQ, ligne 276 point 9](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/276-a-298-2-revenu-imposable/ligne-276/) et [annexe N 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.N%282025-12%29.pdf) : 290 à N52, N64 vers 276; ajustement ajouté à l'imposable, pas au net. 252 limité au surplus après N18 **et N54**; clôture N80 = N70 + 260 + 276 − 252. Ce solde de frais est distinct des pertes en capital.
- [Annexe F 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.F%282025-12%29.pdf) : les reports de pertes 25300/290 ne réduisent pas le gain inclus au revenu total ni l'assiette FSS. Les crédits fondés sur le revenu net restent fondés sur ce revenu, pas sur l'imposable après pertes.

**Périmètre accepté avant implémentation :** un parcours 3D confirmé, avec
ou sans emploi ordinaire et frais 3E validés. Historique exhaustif par année
**2004 à 2024**, soldes fédéral et Québec indépendants, déjà nets au taux
de 50 % (jamais des pertes brutes), après toutes utilisations antérieures.
Avis de cotisation/recotisation ARC et RQ, anciennes annexes 3/G, TP-729 et
registre des utilisations requis, avec confirmation distincte. Demandes
2025 explicites et indépendantes; consommation automatique chronologique
dans chaque juridiction, jamais de maximisation ni de copie d'un solde.
Si aucun solde : historique vide confirmé. Le dossier 3D fournit seul le
gain/perte courant; aucune saisie manuelle en double de la perte 2025.

Le revenu total, net, retenues et FSS restent inchangés par 3F. Seuls les
imposables diminuent de 25300 et de 290 − 276. Refus d'un imposable négatif
ou d'un profil demandant de déduire plus que le gain ou le solde. Une
demande 252 devenue excessive à cause de N52 est refusée, jamais réduite
silencieusement. Le rajustement 276 est ajouté au solde distinct de frais
3E, sans conserver simultanément la perte en capital déjà consommée.

Perte nette 2025 : aucun report utilisé en 2025, ajout unique à une ligne
2025 du registre de clôture prospectif, provisoire à rapprocher des futurs
avis. Recalcul et rechargement partent toujours des soldes d'ouverture
immuables; aucune nouvelle consommation ni double ajout. Les résultats ne
constituent ni un TP-729/T1A officiel ni une déclaration transmise.

**Refus explicites :** soldes avant 2004 (dont 1985 et taux historiques),
PDTPE/ABIL convertie, biens précieux/personnels, exonérations, réserves,
décès, étranger, conjoint, pertes apparentes, plusieurs ventes 2025,
réorganisations, solde incertain, années dupliquées, corrections pendantes,
IMR non couvert et report rétrospectif (T1A/TP-1012.A). Les possibilités
légales de report rétrospectif sont documentées mais ne sont pas calculées.
Tous les garde-fous 3D/3E restent actifs; leurs indicateurs de reports non
traités restent bloquants, le profil distinct 3F étant l'unique chemin validé.
Arrêt après 3F, sans commencer 3G.

**Validation de livraison 3F :** 100 nouveaux tests ciblés (87 moteur et
persistance, 13 GUI). Conservation des soldes dans chaque juridiction,
plafonds au cent, ancienneté, revenu net et FSS inchangés, crédit d'âge,
annexe N 276/252 et absence de double report après rechargement vérifiés.
Les modifications du dossier, de la vente, des frais ou du registre
révoquent les confirmations; une ancienne estimation ne peut plus être
exportée et son PDF n'est plus associé au dossier sauvegardé.

Inspection visuelle réelle du formulaire en 600 × 400 et 1000 × 700,
en haut, au milieu et en bas : champs accessibles et boutons fixes visibles.
Quatre PDF synthétiques inspectés intégralement (10 pages) : gain, perte
2025, interaction annexe N et registre complet 2004–2024. Le registre
compact présente explicitement ouverture / utilisé / clôture et évite
une page finale isolée dans le scénario de perte. Artefacts uniquement
dans `tmp/`, exclus de Git, notamment `tmp/integrate_3f.py`.

Suite complète finale : `python -m pytest -q`, **3 024 tests réussis**,
8 avertissements de dépréciation, aucun test supprimé ou désactivé.
Sous Windows, des initialisations Tcl/Tk intermittentes ont échoué lors
des premières exécutions avec chemins forcés; l'exécution finale complète
a réussi avec la découverte native, sans `TCL_LIBRARY` ni `TK_LIBRARY`.


### Bloc 3G — placements et impôts étrangers 2025

Audit et livraison sur le socle 3F `2b0a34d`. Le périmètre reste volontairement
conservateur : **un seul pays étranger, un seul titulaire, revenu de placement
non commercial, montants déjà convertis et validés en CAD**, avec une paire
T5/RL-3 cohérente. Les cas multi-pays, comptes conjoints, pensions étrangères,
revenus d'entreprise, gains en capital étrangers, conventions ou exemptions
ambiguës et conversions implicites restent exclus.

Le parcours reconnaît le revenu étranger brut T5 **case 15** et l'impôt étranger
payé T5 **case 16**, avec contreparties Québec RL-3 **F/G**. Le revenu brut est
ajouté une seule fois à la ligne fédérale **12100** et à la ligne Québec
**130**. L'impôt étranger n'est jamais soustrait du revenu brut et n'est jamais
traité comme une retenue canadienne.

Les crédits pour impôt étranger suivent une approche de confirmation humaine :
le moteur **ne reconstruit pas automatiquement** les formulaires complexes.
La ligne fédérale **40500** doit provenir d'un **T2209 2025 vérifié** et la ligne
Québec **409** d'un **TP-772 2025 vérifié**, avec références de source
conservées. Les crédits sont non remboursables, plafonnés par l'impôt restant
dans chaque juridiction; le crédit Québec est en plus borné par l'impôt
étranger payé diminué du crédit fédéral confirmé.

La cotisation au Fonds des services de santé Québec est recalculée à la ligne
**446** sur le revenu de placement étranger de la ligne 130, selon le barème
2025 déjà utilisé par les autres revenus de placement. Les obligations de
déclaration de biens étrangers **T1135** et **TP-1079.8.BE** sont explicitement
signalées et doivent être vérifiées séparément; elles ne sont ni déterminées
ni produites automatiquement par le moteur.

La chaîne locale 3G est intégrée de bout en bout : validation du profil,
calcul 12100/130, FSS 446, crédits 40500/409, résumé, trace de calcul, rapport
PDF, sauvegarde JSON, rechargement et formulaire GUI défilant. Le formulaire
demande pays, source, devise, références T2209/TP-772, montants de crédits et
confirmation des obligations de biens étrangers. Toute modification pertinente
révoque les confirmations; appliquer un nouveau profil invalide l'estimation
et bloque l'export de l'ancien PDF. Les anciens JSON sans profil 3G chargent
des profils vides.

Le parcours 3G initial est exclusif des autres placements et des parcours
pensions/prestations couverts actuellement. En particulier, le T5 étranger
a priorité sur le parcours T5 de rente lorsque les cases 15/16 et RL-3 F/G
sélectionnent explicitement 3G. Les combinaisons avec intérêts canadiens,
dividendes, gains en capital, frais de placement, reports de pertes, retraits,
pensions ou prestations restent réservées au futur Bloc 3H.

**Validation de livraison 3G : 70 nouveaux tests** (53 moteur/persistance/
trace/PDF et 17 GUI). Les tests couvrent l'appariement T5/RL-3, garde-fous
CAD/pays/titulaire, limites des crédits, FSS, sauvegarde/rechargement,
révocation des confirmations, invalidation d'un PDF périmé et réouverture
complète du dossier. Le formulaire a été contrôlé à 96/144/192 DPI avec
fenêtres 600 × 400 et 1000 × 700.

Contrôle de non-régression ciblé : **549 tests réussis**, 5 avertissements.
Suite complète finale `python -m pytest -q` : **3 094 tests réussis**,
8 avertissements de dépréciation existants, aucun échec, aucun test retiré
ou désactivé (120,62 s en local). Les avertissements SWIG/PyMuPDF et
`openpyxl` sont préexistants et non bloquants. Le Bloc 3G est clos; la
première combinaison contrôlée est livrée dans 3H-A ci-dessous.


### Bloc 3H-A — combinaison contrôlée intérêts + dividendes canadiens 2025

Première ouverture du Bloc 3H sur le socle 3G `5ab4086`. Le périmètre reste
volontairement étroit : **une même paire T5/RL-3**, un seul titulaire, montants
CAD, avec intérêts canadiens T5 **13** / RL-3 **D** et dividendes canadiens
T5 **10/11/12/24/25/26** / RL-3 **A1/A2/B/C**. Les deux profils doivent être
confirmés explicitement; une simple présence de cases ne détourne pas les
parcours historiques 3A ou 3C.

Le moteur applique successivement les intérêts et les dividendes sans double
compter le revenu. Les lignes fédérales **12100** et **12000/12010**, ainsi que
les lignes Québec **130**, **128**, **166** et **167**, conservent les règles
déjà validées dans 3A et 3C. Les crédits pour dividendes fédéral **40425** et
Québec **415** restent appliqués séparément.

La cotisation au Fonds des services de santé Québec est recalculée une seule
fois sur une assiette globale du parcours combiné :
**ligne 130 intérêts + lignes 166 + 167 dividendes réels**. La majoration des
dividendes incluse à la ligne 128 est donc exclue de cette assiette. Le résultat
global est porté une seule fois dans le rapprochement afin d'éviter toute
double cotisation. Un cas synthétique de 10 000 $ d'intérêts et 10 000 $ de
dividendes réels donne une assiette FSS de 20 000 $ et une cotisation de
**18,70 $**, alors que chaque composante prise isolément demeure sous le seuil.

La chaîne locale 3H-A est intégrée de bout en bout : détection prudente,
consolidation, estimation, rapprochement, résumé, trace de calcul, rapport PDF,
sauvegarde JSON, rechargement et formulaire GUI dédié
« Intérêts + dividendes 2025 (3H-A) ». Modifier les sources du formulaire
révoque les deux confirmations; appliquer une nouvelle combinaison invalide
l'estimation et empêche l'export du PDF précédent.

Le stockage conserve les deux profils existants plutôt que d'introduire un
nouveau schéma JSON. À la sauvegarde et au rechargement, la présence simultanée
des profils intérêts et dividendes confirmés est validée par le consolidateur
3H-A. Les anciens dossiers 3A/3C continuent d'utiliser leurs garde-fous
historiques lorsqu'un seul profil est confirmé.

Les autres combinaisons restent exclues de 3H-A : intérêts/dividendes avec
gains ou pertes en capital, reports de pertes, placements étrangers, pensions,
retraits ou prestations. Les frais de placement sont désormais ouverts
séparément par le Bloc 3H-B ci-dessous; les autres combinaisons devront conserver
leurs interactions propres, notamment FSS globale, récupérations AE/PSV, crédits,
annexe B et RAMQ.

La détection 3H-A est tolérante aux `Decimal` non finis (`NaN`, `sNaN`,
`Infinity`) afin de ne pas lever `decimal.InvalidOperation` avant les
validateurs métiers responsables des montants invalides. Cette correction
préserve les erreurs métier attendues dans les parcours RRQ/RPC, PSV et
pensions.

**Validation de livraison 3H-A : 26 nouveaux tests** (23 moteur/stockage/
trace/PDF et 3 GUI). Contrôles ciblés : 36 tests GUI + stockage, 312 tests
moteur/GUI élargis et **247 tests GUI** exécutés ensemble. Suite complète
finale `python -m pytest -q` : **3 120 tests réussis**, 8 avertissements de
dépréciation existants, aucun échec et aucune erreur (108,56 s en local).
Les avertissements SWIG/PyMuPDF et `openpyxl` restent non bloquants.

Le Bloc 3H n'est donc plus vide : **3H-A est livré**. Les prochaines
combinaisons 3H devront rester incrémentales et être validées une par une.

### Bloc 3H-B — intérêts + dividendes canadiens + frais de placement 2025

Le Bloc 3H-B prolonge 3H-A sans créer un nouveau profil fiscal : les deux
profils confirmés intérêts/dividendes sont combinés avec le profil existant
des frais de placement 3E. Le périmètre reste volontairement étroit : aucune
combinaison simultanée avec gains/pertes en capital, reports 3F, placements
étrangers 3G, pensions, retraits ou prestations.

Les déductions de frais conservent les règles validées en 3E : ligne fédérale
**22100**, ligne Québec **231** et revenus de l’annexe N ligne 36 fondés sur
les intérêts ligne 130 et les dividendes imposables ligne 128. Les frais de
transaction demeurent exclus et les confirmations existantes restent liées
au dossier et aux profils de placement par empreinte.

Pour la FSS Québec, 3H-B recalcule une seule assiette finale : **ligne 130 +
lignes 166 + 167 - ligne 231**. La majoration des dividendes n’entre pas dans
cette assiette et le report de frais ligne 252 n’a aucun effet sur la FSS.
La cotisation finale est portée une seule fois dans le résultat intérêts; le
résultat dividendes conserve une cotisation nulle afin d’éviter tout double
comptage dans le rapprochement.

Cas synthétique validé : 10 000 $ d’intérêts, 10 000 $ de dividendes réels et
1 500 $ de frais admissibles donnent une assiette FSS de **18 500 $** et une
cotisation de **3,70 $**. Avec 1 870 $ de frais, l’assiette redescend au seuil
de 18 130 $ et la cotisation FSS devient nulle.

La persistance JSON réutilise les trois profils existants. Sauvegarde,
rechargement et recalcul produisent le même résultat. Le résumé écran, la
trace et le rapport PDF identifient explicitement le **Bloc 3H-B** et utilisent
l’assiette FSS après frais. Le parcours 3H-A reste inchangé lorsqu’aucun frais
de placement n’est confirmé.

Dans l’interface, l’utilisateur valide d’abord « Intérêts + dividendes 2025
(3H-A) », puis ouvre le formulaire « Frais de placement 2025 (3E) ». Lorsque
ce profil est confirmé, le calcul bascule vers 3H-B. Toute modification des
frais invalide l’estimation précédente et bloque l’export d’un PDF périmé.

**Validation de livraison 3H-B : 10 nouveaux tests** couvrant moteur, FSS,
refus du capital additionnel, sauvegarde/rechargement, recalcul, résumé, trace,
PDF et GUI. Contrôle ciblé élargi : **215 tests réussis**, 5 avertissements.
Suite complète finale `python -m pytest -q` : **3 130 tests réussis**,
**8 avertissements** de dépréciation existants, aucun échec ni erreur
(109,90 s en local). Les avertissements SWIG/PyMuPDF et `openpyxl` restent
non bloquants.

Le Bloc 3H-B est donc livré. Les prochaines combinaisons 3H restent à ouvrir
progressivement, avec validation explicite de leurs interactions propres.

### Bloc 3H-C — intérêts + dividendes canadiens + capital 2025

Le Bloc 3H-C prolonge la combinaison contrôlée 3H-A avec le parcours capital
simple déjà validé en 3D : une paire T5/RL-3 contenant intérêts et dividendes
canadiens, plus une vente unique d'actions canadiennes documentée par une paire
T5008/RL-18 et un profil capital confirmé. Aucun nouveau schéma de stockage n'est
introduit : les profils intérêts, dividendes et capital existants sont réutilisés.

Le revenu total ajoute le gain imposable fédéral 12700 / Québec 139 au résultat
des intérêts et dividendes. La FSS Québec est recalculée une seule fois sur
**130 + 166 + 167 + 139**. La majoration des dividendes demeure exclue et la
cotisation globale est portée uniquement par le résultat intérêts afin d'éviter
tout double comptage. Le résultat dividendes et le résultat capital conservent
donc une FSS nulle dans cette combinaison.

Une perte en capital 2025 ne réduit ni les intérêts ni les dividendes courants.
Dans ce cas, la ligne 139 demeure nulle et la perte nette calculée reste suivie
séparément pour les mécanismes de reports; 3H-C n'ouvre pas automatiquement 3F.

Cas synthétique validé : 10 000 $ d'intérêts, 10 000 $ de dividendes réels et
une vente donnant un gain de 2 440 $, donc un gain imposable de 1 220 $, donnent
une assiette FSS de **21 220 $** et une cotisation de **30,90 $**. Avec une vente
produisant une perte nette de 530 $, la ligne 139 reste à zéro; l'assiette FSS
demeure **20 000 $** et la cotisation **18,70 $**.

Le stockage autorise maintenant la sauvegarde et le rechargement simultanés des
trois profils. Le recalcul après rechargement reproduit le même revenu, le même
capital et la même FSS. Le résumé écran, la trace de calcul et le PDF identifient
explicitement le **Bloc 3H-C** et présentent la formule d'assiette globale.

Dans l'interface, un profil capital validé peut prolonger une combinaison 3H-A
déjà confirmée sans effacer les profils intérêts/dividendes. Toute modification
du capital invalide l'estimation précédente et bloque l'export d'un PDF périmé.
Les frais de placement 3E, reports de pertes 3F, placements étrangers 3G,
pensions, retraits et prestations restent exclus de 3H-C à ce stade.

**Validation de livraison 3H-C : 11 nouveaux tests** couvrant moteur, FSS globale,
gain/perte en capital, refus des frais additionnels, sauvegarde/rechargement,
recalcul, résumé, trace, PDF, GUI, persistance et invalidation. Contrôles ciblés
successifs : 247, 266, 161 puis **168 tests réussis** selon les sous-ensembles.
Suite complète finale `python -m pytest -q` : **3 141 tests réussis**, **8
avertissements** de dépréciation existants, aucun échec ni erreur (103,31 s en
local). Les avertissements SWIG/PyMuPDF et `openpyxl` restent non bloquants.

Le Bloc 3H-C est livré et validé par la suite locale et le CI GitHub.
Les combinaisons 3H suivantes restent ouvertes progressivement.

### Bloc 3H-D — intérêts + dividendes + capital + frais de placement 2025

Le Bloc 3H-D prolonge 3H-C avec le profil de frais de placement déjà couvert par
3E. Il combine donc une paire T5/RL-3 validée pour intérêts et dividendes, une
vente simple T5008/RL-18 validée en 3D, puis des frais de gestion/garde
documentés. Aucun nouveau schéma de stockage n'est introduit : les quatre profils
existants sont réutilisés.

Le revenu total conserve les intérêts, les dividendes imposables et le gain
imposable. Les déductions de frais restent appliquées aux lignes fédérale 22100
et Québec 231. L'assiette FSS globale devient **130 + 166 + 167 + 139 - 231**.
La majoration des dividendes demeure exclue et le report Québec 252 ne réduit
pas cette assiette. La cotisation finale est portée uniquement par le résultat
intérêts; dividendes et capital conservent une FSS nulle afin d'éviter tout
double comptage.

Le périmètre initial reste volontairement prudent : les intérêts d'emprunt sont
refusés lorsqu'un parcours capital est présent. Seuls les frais de gestion/garde
documentés sont ouverts dans 3H-D. Les reports de pertes 3F, placements
étrangers 3G, pensions, retraits et prestations restent exclus de cette
combinaison.

Cas synthétique validé : 10 000 $ d'intérêts, 10 000 $ de dividendes réels,
1 220 $ de gain imposable et 1 500 $ de frais donnent une assiette FSS de
**19 720 $** et une cotisation de **15,90 $**. Avec une perte en capital, la
ligne 139 reste nulle; les frais de 1 500 $ abaissent l'assiette de 20 000 $ à
**18 500 $**, pour une FSS de **3,70 $**. La perte en capital ne réduit pas les
intérêts ni les dividendes courants.

La persistance JSON sauvegarde et recharge simultanément les quatre profils.
Le recalcul après rechargement reproduit le même revenu, le même capital, les
mêmes frais et la même FSS. Une empreinte de frais incohérente est refusée.
Le résumé écran, la trace de calcul et le PDF identifient explicitement le
**Bloc 3H-D** et affichent l'assiette après frais. Dans l'interface, le formulaire
des frais signale le contexte 3H-D; toute modification des frais invalide
l'estimation et bloque l'export d'un PDF périmé.

**Validation de livraison 3H-D : 10 nouveaux tests nets** couvrant moteur,
FSS globale, exclusion des intérêts d'emprunt avec capital, sauvegarde et
rechargement, recalcul, empreinte des frais, résumé, trace, PDF, perte en
capital, GUI, persistance et invalidation. Contrôles ciblés successifs :
**255**, **274**, **282** puis **291 tests réussis**, avec 5 avertissements de
dépréciation existants selon les sous-ensembles.

Suite complète finale `python -m pytest -q` : **3 151 tests réussis**,
**8 avertissements** de dépréciation existants, aucun échec ni erreur
(**102,87 s** en local). Les avertissements SWIG/PyMuPDF et `openpyxl` restent
non bloquants.


### Bloc 3H-E — intérêts + dividendes + capital + reports de pertes 2025

Le Bloc 3H-E prolonge 3H-C avec le profil de reports de pertes en capital déjà
couvert par 3F. Il combine une paire T5/RL-3 validée pour intérêts et
dividendes, une vente simple T5008/RL-18 validée en 3D, puis des soldes de
pertes antérieures confirmés. Aucun nouveau schéma de stockage n'est introduit :
les profils existants intérêts, dividendes, capital et reports sont réutilisés;
le profil de frais doit rester vide dans ce bloc.

Les reports fédéraux 25300 et Québec 290 réduisent uniquement le revenu
imposable, dans les plafonds et soldes déjà contrôlés par 3F. Ils ne modifient
ni le revenu total, ni le revenu net, ni l'assiette FSS. L'assiette FSS globale
reste donc **130 + 166 + 167 + 139**, avec exclusion de la majoration des
dividendes. La cotisation finale reste portée une seule fois par le résultat
intérêts; dividendes et capital conservent une FSS nulle.

Cas synthétique validé : 10 000 $ d'intérêts, 10 000 $ de dividendes réels et
1 220 $ de gain imposable donnent un revenu total/net de **23 870 $**. Une
demande de reports de **1 000 $** au fédéral et **800 $** au Québec ramène le
revenu imposable à **22 870 $** et **23 070 $** respectivement, sans modifier
l'assiette FSS de **21 220 $** ni la cotisation de **30,90 $**. Une demande
supérieure au gain admissible demeure refusée par les plafonds de 3F.

Le périmètre reste volontairement contrôlé : les frais de placement combinés
aux reports sont réservés au futur Bloc **3H-F** afin d'isoler les interactions
des lignes 231, 252, 276 et 290 de l'annexe N. Les placements étrangers 3G,
pensions, retraits, prestations et autres parcours combinés restent exclus de
3H-E.

La persistance JSON sauvegarde et recharge les profils intérêts, dividendes,
capital et reports, puis reproduit le même revenu, les mêmes reports et la même
FSS au recalcul. Une empreinte de reports altérée est refusée. Le résumé écran,
la trace de calcul et le PDF identifient explicitement le **Bloc 3H-E** et
indiquent que 25300/290 n'ont aucun effet sur la FSS. Dans l'interface, le
formulaire 3F reconnaît le contexte 3H-E; toute modification des reports
invalide l'estimation précédente et bloque l'export d'un PDF périmé.

**Validation de livraison 3H-E : 12 nouveaux tests nets** couvrant moteur,
plafonds des reports, FSS inchangée, exclusion frais + reports, sauvegarde et
rechargement, recalcul, empreinte des reports, résumé, trace, PDF, GUI,
persistance et invalidation. Les contrôles ciblés ont atteint successivement
**237**, **258**, **266** puis **290 tests réussis**, avec 5 avertissements de
dépréciation existants selon les sous-ensembles.

Suite complète finale `python -m pytest -q` : **3 163 tests réussis**,
**8 avertissements** de dépréciation existants, aucun échec ni erreur
(**101,82 s** en local). Les avertissements SWIG/PyMuPDF et `openpyxl` restent
non bloquants.


### Bloc 3H-F — intérêts + dividendes + capital + frais + reports de pertes 2025

Le Bloc 3H-F réunit les parcours déjà validés 3H-D et 3H-E : intérêts et
dividendes canadiens sur une paire T5/RL-3, une vente simple T5008/RL-18,
des frais de placement 3E et des reports de pertes en capital 3F. Aucun nouveau
schéma de stockage n'est ajouté; les profils existants sont combinés et leurs
empreintes restent vérifiées.

Le périmètre initial conserve seulement les frais de gestion/garde documentés
lorsqu'un gain ou une perte en capital est présent. Les intérêts d'emprunt avec
capital restent refusés. Les placements étrangers, pensions, retraits,
prestations et autres parcours combinés restent exclus.

L'ordre de calcul est contrôlé : les revenus de placement alimentent d'abord le
revenu, puis la ligne 231 réduit le revenu net Québec et l'assiette FSS. Les
reports 25300/290 réduisent ensuite le revenu imposable seulement. Les lignes
252 et 276 de l'annexe N restent distinctes afin d'éviter toute double
utilisation d'un report. Pour 3H-F, le rajustement 276 s'appuie sur le revenu
de placement N36 global de la combinaison, et non sur la seule ligne 139 du
capital.

Cas synthétique principal : 10 000 $ d'intérêts, 10 000 $ de dividendes réels,
1 220 $ de gain imposable, 1 500 $ de frais de gestion, puis des reports de
1 000 $ au fédéral et 800 $ au Québec. Le revenu total reste **23 870 $**,
le revenu net devient **22 370 $** dans les deux juridictions, puis le revenu
imposable devient **21 370 $** au fédéral et **21 570 $** au Québec.
L'assiette FSS reste **19 720 $** et la cotisation **15,90 $**; les reports
25300/290 et les mouvements 252/276 n'ajoutent aucune seconde réduction de FSS.

Un scénario annexe N avec solde Québec de frais, ligne 252 et ligne 290 vérifie
que les deux mécanismes restent séparés. Un scénario de frais très élevés
vérifie aussi le rajustement 276 calculé sur le N36 global et l'absence de
revenu imposable Québec négatif. Une demande 252 excessive après prise en
compte de la perte 290 reste refusée.

La persistance JSON sauvegarde et recharge les cinq profils de la combinaison
(intérêts, dividendes, capital, frais et reports), puis reproduit le même
revenu, les mêmes frais, les mêmes reports et la même FSS au recalcul. Le
résumé écran, la trace de calcul et le PDF identifient explicitement le
**Bloc 3H-F**. Dans l'interface, le formulaire 3F reconnaît le contexte 3H-F;
toute modification des reports invalide l'estimation et le PDF antérieurs.
Une modification des frais révoque les confirmations de reports afin de forcer
leur revalidation avec la nouvelle annexe N.

**Validation de livraison 3H-F : 9 nouveaux tests nets** depuis 3H-E. Les
contrôles ciblés ont atteint **361 tests réussis**, puis **414 tests réussis**;
le lot GUI élargi a atteint **328 tests réussis**, chaque fois avec
**5 avertissements** de dépréciation existants.

Suite complète finale `python -m pytest -q` : **3 172 tests réussis**,
**8 avertissements** de dépréciation existants, aucun échec ni erreur
(**104,98 s** en local). Les avertissements SWIG/PyMuPDF et `openpyxl` restent
non bloquants.

## Priorité 4 — audit et découpage des déductions restantes 2025

Audit initial après la livraison de 3H-F sur le socle
`89b8a5666b74afdd0bc7d015e2b8edbb94c3f6c1` (3 172 tests locaux, CI verte).
La Priorité 4 sera livrée par sous-blocs indépendants. Le premier sous-bloc
retenu est **4A — CELIAPP simple**, avant frais de garde, emploi/T2200,
déménagement, pension alimentaire et autres déductions.

### Bloc 4A proposé — CELIAPP simple, ligne 20805 / ligne 215

Le sous-bloc initial couvre uniquement une déduction CELIAPP 2025 simple et
documentée. Le montant fédéral est celui de la ligne 20805 calculée à
l'annexe 15 fédérale. Pour le Québec, la ligne 215 reprend le montant déduit à
la ligne fédérale 20805.

Périmètre initial volontairement limité :

- particulier résident du Canada et du Québec pendant toute l'année 2025;
- CELIAPP ouvert et détenu par le contribuable;
- cotisations directes en argent effectuées du 1er janvier au 31 décembre 2025;
- aucune cotisation inutilisée d'une année antérieure réclamée dans ce premier
  sous-bloc;
- aucun transfert REER vers CELIAPP;
- aucun retrait admissible, retrait imposable, retrait désigné ou transfert
  désigné en 2025;
- aucun excédent CELIAPP ni impôt mensuel sur excédent;
- montant de déduction 2025 confirmé à partir de l'annexe 15 / des pièces du
  contribuable, avec source conservée localement;
- déduction appliquée au revenu net et imposable fédéral et Québec, sans
  modifier le revenu total, les retenues ou les revenus de placement.

Les cas de cotisations inutilisées reportées, transferts REER→CELIAPP,
retraits admissibles, retraits imposables (notamment ligne 12905), retraits
désignés, excédents, décès, non-résidence ou situations multi-années seront
refusés explicitement dans 4A et réservés à un sous-bloc ultérieur.

### Contrat technique visé pour 4A

Le bloc doit suivre les mêmes garde-fous que les déductions déjà intégrées :

1. profil immuable dédié avec montant demandé, montant disponible confirmé,
   source et confirmations d'absence des cas exclus;
2. validation stricte des montants finis, non négatifs et du plafond confirmé;
3. application unique de la déduction sur les revenus net/imposable fédéral
   et Québec;
4. persistance JSON rétrocompatible sans migration de schéma obligatoire;
5. résumé, trace de calcul et PDF indiquant explicitement les lignes
   **20805 / 215**;
6. formulaire GUI local avec révocation de confirmation dès qu'un champ change;
7. invalidation de l'estimation et de l'ancien PDF après modification;
8. tests moteur, limites, persistance, recalcul, trace/PDF et GUI avant
   ouverture d'un sous-bloc 4B.

Aucune transmission fiscale n'est ajoutée : ComptaPrivée AI reste un moteur
local d'estimation et de préparation.

### Bloc 4B proposé — frais de garde fédéraux, T778 / ligne 21400

Le sous-bloc 4B couvre la déduction fédérale 2025 pour frais de garde
d'enfants. Le calcul s'appuie sur le formulaire T778 et le montant admissible
est reporté à la ligne 21400 de la déclaration fédérale. Ce bloc ne crée pas
le crédit d'impôt québécois pour frais de garde : ce crédit remboursable sera
traité séparément dans la priorité consacrée aux crédits Québec.

Périmètre initial volontairement limité :

- services de garde réellement fournis en 2025 et frais payés/documentés;
- contribuable seul à soutenir l'enfant, ou contribuable qui est la personne
  au revenu net le moins élevé du couple;
- aucune demande par la personne au revenu net le plus élevé;
- aucune situation spéciale des parties C ou D du T778 (études, incapacité,
  séparation admissible, détention ou autre exception permettant au conjoint
  au revenu plus élevé de demander tout ou partie de la déduction);
- enfants classés dans les trois catégories de plafond annuel du T778 :
  8 000 $, 5 000 $ ou 11 000 $ selon l'âge et l'admissibilité au crédit
  d'impôt pour personnes handicapées;
- limite de base calculée comme le moindre des frais admissibles payés, du
  total des plafonds annuels applicables aux enfants et des deux tiers du
  revenu gagné du demandeur;
- aucun report de frais inutilisés à une année ultérieure;
- reçus et source de validation conservés localement;
- déduction appliquée uniquement au revenu net et au revenu imposable
  fédéraux; aucun effet automatique sur le revenu net ou imposable Québec.

Les camps avec hébergement, pensionnats, situations de garde partagée,
demandes réparties entre deux contribuables, demandes par le conjoint au
revenu supérieur, décès et parties C/D du T778 sont réservés à un sous-bloc
ultérieur.

### Contrat technique visé pour 4B

Le bloc 4B devra respecter les garde-fous suivants :

1. profil immuable dédié avec frais admissibles, revenu gagné, nombre
   d'enfants par catégorie de plafond, source et confirmations;
2. validation stricte des montants finis/non négatifs et des nombres
   d'enfants entiers/non négatifs;
3. calcul déterministe du plafond enfants, de la limite des deux tiers du
   revenu gagné et de la déduction ligne 21400;
4. application unique de la ligne 21400 au revenu net/imposable fédéral sans
   modifier le revenu total, les retenues, les revenus de placement ni les
   montants Québec;
5. persistance JSON rétrocompatible;
6. résumé, trace de calcul et PDF indiquant explicitement T778 / ligne 21400;
7. formulaire GUI local avec révocation des confirmations dès qu'un champ
   pertinent change et invalidation de l'estimation/PDF antérieurs;
8. tests moteur, limites, arrondis, persistance, recalcul, trace/PDF et GUI
   avant ouverture du sous-bloc 4C.

Aucune transmission fiscale n'est ajoutée. Le montant demeure une estimation
locale à valider à partir du T778 et des pièces justificatives.


### Bloc 4C livré — dépenses d'emploi simples, T2200/T777 et TP-64.3/TP-59

Le bloc 4C couvre un profil volontairement limité d'employé salarié ordinaire
qui réclame des dépenses d'emploi 2025 déjà établies et validées à partir des
formulaires applicables.

Périmètre livré :

- fédéral : montant T777 reporté à la ligne 22900;
- Québec : montant TP-59 reporté à la ligne 207, code 07;
- T2200 confirmé lorsqu'une déduction fédérale est réclamée;
- TP-64.3 confirmé lorsqu'une déduction Québec est réclamée;
- dépenses exigées par le contrat de travail et non remboursées;
- montants fédéral et Québec conservés séparément;
- validation comptable et sources conservées localement;
- application aux revenus net et imposable de la juridiction correspondante,
  sans modifier le revenu total, les retenues ni les autres profils fiscaux.

Les situations suivantes sont explicitement hors périmètre 4C simple :
employé à commission, véhicule ou DPA/CCA, voyages-repas-logement,
bureau à domicile, outils et autres profils spécialisés. Elles nécessitent
un futur traitement avancé des dépenses d'emploi.

Contrat technique livré :

1. profil immuable `DepensesEmploi2025` avec montants, sources et confirmations;
2. validation stricte des montants finis et non négatifs;
3. moteur séparé fédéral/Québec;
4. intégration dans `EstimationFiscale2025`;
5. trace de calcul identifiant T777 / ligne 22900 et TP-59 / ligne 207 code 07;
6. persistance JSON rétrocompatible, avec refus d'une divergence entre le
   profil explicite et celui de l'estimation;
7. formulaire GUI dédié avec révocation automatique des confirmations après
   toute modification pertinente;
8. rapport PDF avec montants et sources validées;
9. tests moteur, estimation, trace, stockage, GUI et PDF.

Validation ciblée finale avant suite complète : **130 tests réussis**,
avec **5 avertissements de dépréciation existants** non bloquants.


### Bloc 4D livré — frais de déménagement simples, T1-M / ligne 21900 et TP-348 / ligne 228

Le bloc 4D couvre un profil volontairement limité d'employé salarié ordinaire
qui réclame des frais de déménagement 2025 déjà établis et validés sur les
formulaires applicables.

Périmètre livré :

- fédéral : montant T1-M reporté à la ligne 21900;
- Québec : montant TP-348 reporté à la ligne 228;
- déménagement effectué pour occuper un emploi à un nouveau lieu de travail;
- nouveau domicile confirmé au moins 40 km plus près du nouveau lieu de travail;
- déménagement à l'intérieur du Canada;
- remboursements ou allocations de l'employeur déjà pris en compte;
- montants fédéral et Québec conservés séparément;
- validation comptable et sources conservées localement;
- application aux revenus net et imposable de la juridiction correspondante,
  sans modifier le revenu total ni les retenues.

Les situations suivantes sont explicitement hors périmètre 4D simple :
travail autonome, étudiant à temps plein, déménagement international,
report de frais d'années antérieures et plusieurs déménagements admissibles.
Elles nécessitent un futur traitement avancé des frais de déménagement.

Contrat technique livré :

1. profil immuable `FraisDemenagement2025` avec montants, sources et confirmations;
2. validation stricte des montants finis et non négatifs;
3. moteur séparé fédéral/Québec;
4. intégration dans `EstimationFiscale2025` après 4C;
5. trace de calcul identifiant T1-M / ligne 21900 et TP-348 / ligne 228;
6. persistance JSON rétrocompatible, avec refus d'une divergence entre le
   profil explicite et celui de l'estimation;
7. formulaire GUI dédié avec révocation automatique des confirmations après
   toute modification pertinente;
8. rapport PDF avec montants et sources validées;
9. tests moteur, estimation, trace, stockage, GUI et PDF.

Validation ciblée finale avant suite complète : **145 tests réussis**,
avec **5 avertissements de dépréciation existants** non bloquants.


### Bloc 4E livré — pension alimentaire payée simple, lignes 21999 / 22000 / 225

Le bloc 4E couvre un profil volontairement limité de pension alimentaire
périodique versée à un conjoint ou ex-conjoint, avec montants déjà établis
et validés.

Périmètre livré :

- fédéral : total payé reporté à la ligne 21999;
- fédéral : partie déductible reportée à la ligne 22000;
- Québec : montant déductible reporté à la ligne 225;
- ordonnance d'un tribunal ou entente écrite confirmée;
- payeur et bénéficiaire vivant séparés au moment du paiement;
- enregistrement ARC confirmé lorsque requis;
- sources fédérale et Québec conservées localement;
- validation comptable obligatoire;
- application de la déduction fédérale et Québec aux revenus net et imposable
  de la juridiction correspondante, sans modifier le revenu total;
- ligne 21999 conservée comme information distincte de la déduction 22000.

Les situations suivantes sont explicitement hors périmètre 4E simple :
pension alimentaire pour enfant, ancien régime ou choix T1157, arrérages ou
paiements rétroactifs, paiement forfaitaire, remboursement de pension,
frais juridiques ou comptables, plusieurs bénéficiaires et année de changement
d'état civil nécessitant un arbitrage avec les crédits personnels fédéraux.

Le pipeline refuse aussi, dans ce profil simple, une combinaison avec une
réclamation active des lignes fédérales 30300, 30400, 30425, 30450 ou 30500.
Ces situations nécessitent une revue fiscale avancée.

Contrat technique livré :

1. profil immuable `PensionAlimentairePayee2025`;
2. validation stricte des montants finis et non négatifs;
3. contrôle ligne 22000 <= ligne 21999;
4. intégration dans `EstimationFiscale2025` après le bloc 4D;
5. garde-fou explicite pour les crédits fédéraux liés;
6. trace de calcul avec ligne informationnelle 21999, déduction 22000 et
   déduction Québec 225;
7. persistance JSON rétrocompatible, avec refus d'une divergence entre le
   profil explicite et celui de l'estimation;
8. formulaire GUI dédié avec révocation automatique des confirmations après
   toute modification pertinente;
9. rapport PDF avec montants et sources validées;
10. tests moteur, estimation, trace, stockage, GUI et PDF.

Validation ciblée finale avant suite complète : **164 tests réussis**,
avec **5 avertissements de dépréciation existants** non bloquants.

### Bloc 4F livré — autres déductions simples, ligne 23200 / ligne 250 code 17

Le bloc 4F applique uniquement des montants déjà établis et validés par le
comptable. Le moteur ne détermine pas automatiquement l'admissibilité détaillée
d'une catégorie de déduction.

Périmètre livré :

- fédéral : déduction à la ligne 23200;
- Québec : déduction à la ligne 250, code 17 à la case 249;
- nature et source documentées séparément pour chaque juridiction concernée;
- validation comptable obligatoire et confirmation des montants déjà établis;
- confirmation qu'aucune autre ligne ou aucun bloc spécialisé ne s'applique;
- application séparée aux revenus net et imposable fédéraux et québécois,
  avec un plancher à zéro et sans modification du revenu total.

Le pipeline comprend un garde-fou anti-double-comptage de la ligne 23200 :
un montant fédéral 4F positif est refusé lorsque cette ligne est déjà utilisée
par les remboursements AE/RQAP ou le bloc des retraits.

Les situations suivantes sont exclues du périmètre 4F simple : remboursements
AE/RQAP, récupération de prestations sociales à la ligne 23500, retraits
REER/T3012A, frais juridiques, remboursement de pension alimentaire,
transferts ou cotisations inutilisées à un régime, soutien aux personnes
handicapées, montants CELIAPP déjà inclus, abris fiscaux, revenu fractionné
et autres traitements spécialisés ou déductions disposant d'une ligne ou
d'un bloc dédié.

Contrat technique livré :

1. profil immuable `AutresDeductions2025` et validation des montants finis
   et non négatifs, des sources, des natures et des confirmations;
2. intégration dans l'estimation fiscale après le bloc 4E;
3. persistance JSON rétrocompatible : un ancien dossier sans
   `autres_deductions` reçoit un profil vide; validation au rechargement et
   refus d'une divergence entre le profil sauvegardé et l'estimation;
4. formulaire GUI dédié, avec révocation des confirmations après modification;
5. trace de calcul distincte pour la ligne 23200 et la ligne 250 code 17,
   avec nature et source par juridiction;
6. rapport PDF présentant les montants, les natures, les sources et les lignes
   fiscales concernées, dont la case 249;
7. tests moteur, estimation, trace, stockage, GUI et PDF.

Validation ciblée finale 21g avant suite complète : **176 passed, 5 warnings**.

### Correctif préalable 5A — lignes 42900 / 40500 / 44000

Sources officielles 2025 revérifiées :

- [T1 Québec 2025, pages 7 et 8](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25f.pdf).
- [Guide ARC 2025, ligne 44000](https://www.canada.ca/en/revenue-agency/services/forms-publications/tax-packages-years/general-income-tax-benefit-package/non-residents/5013-g/guide-non-residents-deemed-residents-federal-non-refundable-tax-credits.html).
  Le guide confirme le facteur de 16,5 % sur 42900; le périmètre logiciel demeure
  celui des résidents du Québec déjà supportés, sans ajout des profils du guide.

`impot_federal_de_base` conserve la ligne 42900 après les crédits ordinaires
et le crédit dividendes 40425, avant 40500. `credit_etranger_ligne_40500`
contient le crédit confirmé utilisable, limité à 42900; la propriété
`impot_federal_apres_credit_etranger` expose le solde avec plancher zéro.
Le rapprochement calcule 44000 sur 42900 exclusivement et retranche cet
abattement remboursable du solde après 40500, sans perdre sa portion remboursable.
Les retenues étrangères ne deviennent pas des retenues canadiennes.

Régression corrigée : pour 42900 = 6 100,30 $, un 40500 utilisable de 100 $
laisse 44000 à 1 006,55 $. Le solde après 40500 est 6 000,30 $ et le résultat
final diminue de 100 $, au lieu de 83,50 $. Trace, résumé et PDF distinguent
les étapes. Aucun changement du schéma JSON : les résultats restent dérivés.

Validation ciblée : **381 passed, 5 warnings**. Tests des bornes du crédit,
de l'abattement remboursable, du dossier sans crédit étranger, de la trace,
du PDF et du rechargement JSON inclus.

Validation complète du préalable : **3465 passed, 8 warnings in 118.44s**.

### Bloc 5A livré — crédit compensatoire fédéral, ligne 34990

Sources officielles 2025 revérifiées avant implémentation :

- [T1 Québec 2025, parties B et C](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25f.pdf).
- [Feuille fédérale 5000-D1, page 7](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).
- [Annexe 9, ligne 22](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.pdf).
- [Annexe 11 propre au Québec, lignes 11 à 17](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
- [Notes explicatives de Finances Canada, exemple du crédit compensatoire](https://fin.canada.ca/drleg-apl/2025/nwmm-amvm-1-n-2-1125-eng.pdf).

Le module pur `tax_federal_top_up_2025.py` distingue les montants admissibles
de 33500 et les crédits de 33800, 34900, 34990 et 35000. Les entrées doivent
être des `Decimal` finis non négatifs; les résultats sont arrondis au cent
(ROUND_HALF_UP). Les lignes inconnues ou dupliquées sont refusées.

```text
33800 = arrondi(33500 × 14,5 %)
34990 = arrondi(max(33800 + Annexe 9 ligne 22 − 8 319,38 $, 0) × 3,45 %)
35000 = 33800 + 34900 + 34990
```

La ligne 33500 regroupe uniquement les montants déjà supportés des lignes
30000, 30100, 30300, 30400, 30425, 30450, 30500, 30800, 31200, 31205,
31260, 31270, 31285, 31400, 31600, 32300 et 33200. Le médical est le montant
après seuil de 33200, et non les frais bruts 33099. La scolarité 32300 est
limitée au montant utilisable sans report selon l'annexe 11 Québec; sa capacité
repose sur la ligne 105, avant scolarité, médical et dons, sans circularité 34990.

Dans le profil de dons actuel, l'annexe 9 ligne 22 est le crédit de 14,5 % sur
les premiers 200 $ réclamés, soit au plus 29 $. Elle ne vaut pas le crédit
total 34900 : pour 1 000 $ de dons, les montants sont respectivement 29 $
et 261 $. Un crédit 33800 de 10 000 $ sans dons donne 34990 = 57,98 $,
comme dans l'exemple officiel. Le revenu imposable n'est pas l'assiette de 34990.

`credits_federaux_complets` expose les bases par ligne et les agrégats T1.
Les champs historiques `base_credits_non_remboursables` et
`credits_non_remboursables` restent les composantes de base emploi.
`top_up_credit` expose désormais le résultat réel 34990. Les fonctions
existantes de crédits conservent leurs validations et leurs limitations;
la finalisation reconstruit le solde depuis l'impôt brut en soustrayant
35000 une seule fois, sans cumuler les débits intermédiaires. Une seconde
finalisation est refusée. L'ordre est 35000, crédit dividendes 40425,
42900, crédit étranger 40500, puis rapprochement avec 44000 calculé sur 42900.
40425 et 40500 n'entrent jamais dans 33800 ni dans 34990.

L'arrondi global de 33800 corrige quelques écarts historiques de 0,01 $ dus
à l'addition de crédits arrondis séparément. Par exemple, 32 286,08 $ de base
donnent 4 681,48 $ à 33800. Les tests conservent des attentes exactes, y compris
pour le rapprochement; le dossier salarié simple de 52 000 $ reste inchangé
(impôt total de 8 088,95 $).

Les huit blocages provisoires au-delà de 57 375 $ sont retirés de
l'orchestrateur pour âge/pension, 30300, 30400, 30425, 31285, 31270,
30450 et 30500. Chacun possède un test au-dessus de ce seuil. Les anciennes
fonctions publiques nommées `integration_*sans_credit_compensatoire*`
restent disponibles pour compatibilité, mais ne pilotent plus l'estimation.
Les mentions de ces blocages dans les sections historiques précédentes sont
remplacées par le comportement décrit ici.

Les autres validations demeurent : admissibilité et confirmation comptable,
cohérence des revenus, liens familiaux, pièces justificatives, exclusions
de partage et de combinaisons familiales, notamment 30400 + 30500.
Aucun report ou transfert de scolarité, report de dons, nouveau crédit
remboursable, profil multi-juridictions ou travail autonome avancé n'est ajouté.
Le fractionnement de pension conserve son périmètre limité et son plafond
de revenu existant; son élargissement n'est pas livré par 5A.

Trace, résumé et PDF affichent 33500, 33800, annexe 9 ligne 22, seuil, taux,
34990 et 35000, même à zéro pour l'audit. Les neuf messages GUI concernés
annoncent le calcul automatique; aucun champ manuel 34990 n'est créé.
Le schéma JSON reste inchangé : les anciens profils sont rechargés et les
résultats dérivés sont recalculés. Le moteur ne détermine pas automatiquement
l'admissibilité détaillée des dépenses ou des personnes.

Validation 5A : **2959 passed, 550 deselected, 5 warnings** pour les tests
fiscaux ciblés. La première suite complète a produit **1 failed, 3508 passed,
8 warnings** : erreur Tcl/Tk `invalid command name "tcl_findLibrary"` pendant
la création de la racine, avant l'ouverture du dialogue médical.

Diagnostic de stabilité, sans modification du code ni des tests Tkinter :

- Deux lancements isolés de
  `test_dialogue_medical_reel_erreur_effacer_et_fermer[780x650]` : chacun
  **1 passed, 5 warnings** (le second après la suite complète).
- Un lancement du fichier `tests/test_gui_layout.py` :
  **28 passed, 5 warnings**.
- Un lancement des fichiers `tests/test_gui*.py`, motif développé explicitement
  sous PowerShell : **275 passed, 5 warnings**.
- Une relance complète avant commits : **3509 passed, 8 warnings in 119.21s**.

L'incident est non reproduit dans ces vérifications. La cause précise de
l'initialisation Tcl/Tk défaillante n'est pas établie; aucune fuite de fixture
ni dépendance à l'ordre n'est démontrée. Aucun test n'a été désactivé ou modifié
pour contourner cet incident.

### Bloc 5B livré — intérêts sur prêts étudiants, ligne 31900

Sources officielles consultées pour 2025 :

- [ARC, ligne 31900](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-31900-interets-payes-vos-prets-etudiants.html).
- [Guide P105 2025, intérêts sur prêts étudiants](https://www.canada.ca/fr/agence-revenu/services/formulaires-publications/publications/p105/p105-etudiants-impot.html).
- [LIR, article 118.62](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.62.html).
- [T1 Québec 2025, page 6, lignes 105 à 122](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25f.pdf).
- [Feuille fédérale 2025, ligne 34990](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).
- [Annexe 11 Québec 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
- [Revenu Québec, crédit distinct pour intérêts étudiants](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/interets-payes-sur-un-pret-etudiant/).

Le contribuable doit être l'emprunteur légal vivant. Le profil exige la
confirmation d'un prêt relevant de la Loi fédérale sur les prêts aux étudiants,
de la Loi fédérale sur l'aide financière aux étudiants, de la Loi sur les prêts
aux apprentis ou d'une loi provinciale/territoriale analogue. Les paiements
retenus sont ceux du contribuable ou d'une personne apparentée confirmée.
Conformément au périmètre prudent fixé pour 5B, les tiers non apparentés et
les liens non établis sont exclus. Le crédit n'est pas transférable.

Les intérêts admissibles n'ont pas de plafond fixe. Les prêts privés, les prêts
combinés, renégociés ou reconsolidés avec un autre prêt, les intérêts de jugement,
les décès et les montants déjà réclamés restent exclus. Les confirmations et
la source sont obligatoires dès qu'un solde positif est renseigné, même si la
réclamation choisie vaut zéro. Un profil vide ne nécessite aucune confirmation.

Pour 2025, les cinq années antérieures sont **2020 à 2024**, auxquelles
s'ajoutent les intérêts payés en 2025. Les reports sont documentés par année et
affectés de la plus ancienne à la plus récente. Les années 2019 et antérieures,
les doublons d'années et les montants invalides sont refusés.

`InteretsPretEtudiant2025` conserve les soldes d'ouverture, leur source et le
montant choisi à réclamer. Le moteur ne choisit pas automatiquement de réclamer
tous les intérêts. Avec une réclamation nulle, les soldes demeurent intacts,
même si l'impôt disponible est nul. Les montants non réclamés sont présentés
par année : le reliquat 2020 expire après 2025; ceux de 2021–2025 restent dans
leur fenêtre en 2026, sans remise à zéro de leur ancienneté. Les soldes saisis
ne sont jamais remplacés par les résultats dérivés lors d'une sauvegarde.

Le montant réclamé est distinct du crédit réellement utilisable. Une
réclamation explicite supérieure au besoin fiscal peut gaspiller des intérêts;
le formulaire et les rapports le signalent. Les montants ainsi réclamés ne sont
pas remis automatiquement en report. Aucun calcul optimal, historique ARC
automatique ou reconstruction de déclarations antérieures n'est proposé.

31900 entre une seule fois dans 33500, puis dans 33800 au taux de 14,5 %.
La T1 2025 fixe ce taux; la mention générale de 15 % encore présente dans P105
n'est pas utilisée pour le calcul 2025. Le moteur 5A recalcule 34990, puis
35000. Aucune déduction supplémentaire de 31900 n'est appliquée au solde
d'impôt. Les revenus total, net et imposable des deux juridictions restent
inchangés. 31900 se situe après la ligne 105 de la T1 Québec et ne change donc
pas cette base utilisée par l'annexe 11 pour la scolarité.

La mesure d'incidence compare le même dossier avec et sans 31900, à autres
entrées constantes. Elle expose les variations de 33800, 34990, 35000 et 42900,
ainsi que l'effet fédéral après 40500 et l'abattement. Le crédit dividendes 40425
reste avant 42900; le crédit étranger 40500 reste après. L'abattement Québec
est toujours de 16,5 % de 42900. Le crédit Québec ligne 385 et son annexe M
sont distincts et restent réservés à la priorité 6.

Les calculs utilisent `Decimal` et l'arrondi au cent du moteur (ROUND_HALF_UP).
Le formulaire défilant permet la saisie des intérêts, des reports 2020–2024,
du montant réclamé et de la source. Chaque modification révoque toutes les
confirmations; une validation réussie invalide l'ancienne estimation et le PDF.
La saisie d'un montant ne vaut jamais reconnaissance automatique d'admissibilité.

La section JSON `interets_pret_etudiant` persiste les données nécessaires au
recalcul, avec les montants en chaînes décimales. Son absence dans un ancien
JSON donne un profil vide. Les clés inconnues du profil et des reports, les
confirmations non booléennes et une divergence avec l'estimation sont refusées.
Trace, résumé et PDF affichent les années effectivement réclamées, la source,
les soldes non réclamés et les incidences calculées.

Validation ciblée : **369 passed, 5 warnings**, dont **84 nouveaux tests 5B**.
Elle couvre également 5A, la scolarité, le stockage, le PDF, l'estimation et
le correctif 40500/42900. Aucun test existant n'a été assoupli.


### Bloc 5C livré — crédit canadien pour la formation, ligne 45350

Sources 2025 vérifiées :
- [ARC 45350](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-45350-canada-training-credit.html).
- [Annexe 11 Québec 2025, lignes 1 à 17](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
- [LIR 122.91](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.91.html), disposition introduite en 2019 : plafond annuel basé sur l'année antérieure, accumulation maximale de 250 $ par an.
- [Annexe T 2025, lignes 40.6 et 40.7](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.T%282025-12%29.pdf).

Le CCF est remboursable. Le contribuable doit avoir de 26 à 65 ans à la fin
2025, résider au Canada toute l'année et produire sa déclaration. Frais
canadiens admissibles et plafond du dernier avis ARC sont documentés et
confirmés. Le moteur ne reconstitue pas l'admissibilité des établissements
ou l'historique ARC. Le plafond maximal possible en 2025 est de 1 500 $,
déduit des six accumulations annuelles possibles; le plafond à vie de
5 000 $ n'est pas un solde disponible présumé pour 2025.

Décision de périmètre : choisir de réclamer le maximum calculé, ou ne rien
réclamer. Les réclamations partielles choisies, décès, faillites, reports et
transferts nécessitent des blocs ultérieurs. Ces limites logicielles ne sont
pas des exclusions fiscales. Les frais admissibles restent validés selon le
profil simple scolarité existant; une combinaison où le CCF dépasse les frais
Québec saisis est refusée plutôt que traitée implicitement.

Formule : minimum du plafond confirmé et de 50 % des frais canadiens.
Les frais bruts restent persistés. 45350 réduit les frais disponibles pour
32300 et la base Québec 398; le seuil de 100 $ reste vérifié sur les frais
bruts. 33800 et 34990 sont recalculés à partir de la base fédérale réduite.
45350 est ensuite ajouté une seule fois aux paiements du rapprochement,
après le calcul de l'impôt; il ne réduit ni le revenu ni directement 42900.
Le principe de l'abattement 44000 sur 42900 avant 40500 reste inchangé.

La GUI scolarité contient les champs formation et le choix de réclamation.
Une modification des frais, sources, âge, plafond ou choix révoque les
confirmations scolarité et formation. Aucun crédit calculé n'est saisi.
La section JSON imbriquée `frais_scolarite.formation` conserve seulement les
entrées; ancien JSON sans cette section = profil vide. Les clés inconnues,
confirmations non booléennes, montants non finis/négatifs et divergences avec
l'estimation sont refusés. Trace et PDF présentent 45350, sa source et la
réduction des frais dans les deux juridictions. Le crédit reste remboursable
même si aucun impôt n'est disponible.

Validation 5C : **171 passed, 5 warnings** en ciblé; suite complète
**3648 passed, 8 warnings** (`pytest --capture=sys -q`). Aucun test existant
modifié, aucun skip/xfail ajouté, configuration pytest inchangée.


### Bloc 5D livré — supplément remboursable pour frais médicaux, ligne 45200

Sources officielles 2025 :
- [Feuille fédérale 5000-D1, page 9](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).
- [ARC, ligne 45200](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-45200-refundable-medical-expense-supplement.html).

Règles : au moins 18 ans fin 2025, résidence au Canada toute l'année,
base 21500 ou 33200 positive, revenu de travail admissible d'au moins
4 390 $. Le supplément est le minimum de 1 504 $ et de 25 % de la base
médicale, diminué de 5 % du revenu familial ajusté dépassant 33 294 $,
avec plancher zéro. Les mêmes frais restent admissibles au crédit médical
non remboursable. Les calculs utilisent Decimal et l'arrondi au cent.

Périmètre logiciel de ce sous-bloc : individu sans conjoint ni personne à
charge, revenu de travail limité à 10100 moins 20700, 21200 et 22900,
sans assurance-salaire, travail autonome, ajustements PUGE/REEI, lignes
21500/23100, décès ou faillite. Ces restrictions ne constituent pas des
exclusions fiscales générales. Les crédits familiaux actifs incompatibles
avec ce profil sont refusés. Les conditions et pièces sont confirmées par
le comptable; le moteur ne déduit pas automatiquement l'admissibilité.

Le revenu familial du profil est 23600; la base médicale provient de 33200
calculée après seuil, et non des frais bruts. 45200 rejoint une seule fois
les paiements du rapprochement, cumulable avec 45350. Revenus, impôt brut,
33800/34990/35000, 40500 et abattement Québec restent inchangés par 45200.

La GUI médicale ajoute âge, source, choix de demande et confirmations.
Toute modification révoque les confirmations. Aucun crédit dérivé n'est
saisi. JSON conserve `frais_medicaux.supplement`, uniquement les entrées;
ancien JSON sans profil = profil vide. Types/confirmations/clés inconnues
et divergence profil-estimation sont contrôlés. Trace et PDF montrent les
opérandes, seuils, plafond, réduction, résultat et source comptable.

Validation ciblée : **274 passed, 5 warnings**. Tests des seuils, arrondis,
entrées invalides, interactions formation/crédit étranger, ancien JSON,
contradictions familiales, GUI et limites de page PDF. Aucun test existant
modifié et aucune modification de la configuration pytest.

Suite complète 5D : **3733 passed, 8 warnings** avec `--capture=sys`.


### Bloc 5E livré — ACT Québec, lignes fédérales 45300 et 41500

Sources 2025 : [annexe 6 propre au Québec, 5005-S6](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s6/5005-s6-25e.pdf)
et [T1 Québec, pages 7–8](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.pdf).

Pour une personne sans conjoint ni personne à charge admissible, l'annexe 6
prévoit une ACT de base de 37,3 % du revenu de travail dépassant 2 400 $,
plafonnée à 3 812,06 $, réduite de 20 % du revenu net ajusté au-delà de
14 170,05 $. Le supplément CIPH utilise 40 % de l'excédent de travail sur
1 200 $, un plafond de 851,31 $, puis une réduction de 20 % au-delà de
33 230,35 $. Chaque résultat est ramené à zéro s'il est négatif.
Admissibilité : résidence au Canada toute l'année, âge minimal 19 ans dans
ce profil; exclusions concernant études à temps plein de plus de 13 semaines,
détention d'au moins 90 jours et exemption diplomatique. Le supplément
requiert l'admissibilité CIPH confirmée. Les cases 10/11 RC210 sont additionnées;
41500 est limité au montant 45300. Un excédent d'avances n'est pas récupéré
par cette formule.

Décision de périmètre : salarié individuel sans conjoint ni personne à charge,
résident du Québec fin 2025, revenu de travail limité à 10100, sans 10400,
bourse imposable, travail autonome, revenu exonéré, ajustement PUGE/REEI,
décès ou faillite. Les exceptions et familles ne sont pas automatiquement
inadmissibles fiscalement; elles nécessitent des blocs distincts. Les profils
familiaux actifs contradictoires sont refusés. Les revenus de travail sont
pris avant déductions, à la différence du supplément médical 45200.

Les choix de base et de supplément sont indépendants. La GUI saisit uniquement
âge, source, avances RC210 et confirmations; aucun montant calculé n'est
saisi. Toute modification révoque les confirmations. L'admissibilité reste
validée par le comptable, sans déduction automatique à partir des seuls revenus.

45300 rejoint les crédits remboursables une seule fois. 41500 augmente l'impôt
net 42000 après les crédits non remboursables : aucune augmentation de 42900
ni de la base de l'abattement 44000. Les revenus, 33800/34990/35000 et 40500
restent inchangés. Trace et PDF exposent source, choix, seuils, réductions,
supplément, RC210, 45300 et 41500, y compris un résultat nul.

Le JSON `allocation_travailleurs` conserve uniquement le profil et les avances
en chaînes décimales à deux décimales. Ancien JSON absent = profil vide;
clés inconnues, types invalides et divergence avec l'estimation sont refusés.

Validation ciblée : **356 passed, 5 warnings**, incluant les blocs 5C/5D,
stockage, estimation, PDF et GUI. Aucun test existant modifié.

Suite complète 5E : **3821 passed, 8 warnings** avec `--capture=sys`.


### Correctif de validation avant les reports de scolarité

Défaut reproduit après 5E : les validateurs médicaux et scolarité acceptaient
`Infinity`; `NaN` déclenchait `InvalidOperation`. Les montants des deux
juridictions doivent désormais être des `Decimal` finis avant les comparaisons.
Les erreurs sont des `ValueError` explicites. Aucune formule, admissibilité,
limite fiscale ni règle d'arrondi n'est modifiée; les montants finis valides
et les anciens JSON restent compatibles. Ce contrôle technique respecte le
contrat Decimal existant, sans introduire de nouvelle règle fiscale.

Régression avant correctif : **32 failed, 2 passed**. Après correctif et
non-régression ciblée : **299 passed, 5 warnings**. Aucun test existant modifié.

Suite complète du correctif : **3855 passed, 8 warnings** (`--capture=sys`).


### Bloc 5F livré — reports fédéraux de scolarité, annexe 11 / ligne 32300

Source : [annexe 11 Québec 2025, lignes 8–17 et 18–25](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
Le solde antérieur provient du dernier avis ARC 2024, y compris les anciens
montants d'études/manuels qui y figurent. La capacité est le revenu imposable
26000 jusqu'à 57 375 $, sinon l'impôt brut divisé par 14,5 %, moins le
sous-total T1 ligne 105, avec plancher zéro. Le report antérieur est utilisé
en premier, puis les frais de 2025 nets du CCF. Leur somme donne 32300;
l'excédent disponible est reporté. La ligne 105 précède 31900 : les intérêts
étudiants ne sont pas soustraits de cette capacité. La réclamation déterminée
par l'annexe n'est pas un montant librement saisi dans le formulaire.

Le profil `reports_federaux` s'active explicitement. Un solde antérieur nul
permet de reporter des frais courants inutilisables. Sans activation, les
anciens garde-fous sont conservés. Solde, avis et source sont validés par le
comptable; aucune reconstitution automatique du compte ARC. Le report futur
est dérivé et doit être rapproché de l'avis ARC après cotisation.

Périmètre 5F : reports fédéraux uniquement, sans transfert entrant/sortant,
sans décès/faillite, ni report Québec. Les deux banques québécoises à 20 %
et 8 % et les transferts sont des fonctions distinctes à venir. Cette limite
logicielle ne nie pas leur admissibilité fiscale. Les frais Québec de 2025
continuent d'exiger une utilisation complète dans le profil antérieur.

L'estimation inclut uniquement le montant utilisé à 32300, une seule fois
dans 33500; 33800/34990/35000 sont recalculés. Revenus et base Québec restent
inchangés. Le CCF réduit les frais courants avant répartition, sans réduire
le solde antérieur. Un dossier contenant seulement un report reste accepté.

GUI : activation, solde de l'avis, source et confirmations; modification de
la scolarité, du CCF ou du report = révocation des confirmations. Aucun solde
futur saisi. JSON ne persiste que les entrées, rétrocompatible si le profil
est absent, avec validation stricte du nouveau profil et contrôle de divergence
avec l'estimation. Trace/PDF distinguent disponible, utilisé et report futur.

Validation ciblée : **281 passed, 5 warnings**, comprenant formation, ACT,
scolarité existante, stockage, trace, PDF et GUI. Aucun test existant modifié.

Suite complète 5F : **3902 passed, 8 warnings** avec `--capture=sys`.


### Correctif — plafond fédéral des dons monétaires ordinaires

L'[annexe 9 de 2025, lignes 6–10](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.pdf)
limite les dons monétaires ordinaires réclamés à 75 % du revenu net 23600.
Les majorations pour dons en nature ne s'appliquent pas au profil monétaire
actuel. Le pipeline ne contrôlait pas ce plafond : 40 000 $ étaient acceptés
avec 51 515 $ de revenu net, alors que le plafond était de 38 636,25 $.

Le pipeline refuse maintenant l'excédent avec un message indiquant le besoin
de report. Il ne supprime aucun don et ne crée pas de report implicitement.
La prise en charge des reports reste une étape distincte. Le contrôle utilise
le revenu net après déductions, sans transposer ce plafond au Québec.

Régression avant correction : **2 failed, 1 passed**. Validation ciblée après
correction : **121 passed, 5 warnings**. Aucun test existant modifié.

Suite complète du correctif dons : **3905 passed, 8 warnings** (`--capture=sys`).


### Bloc 5G livré — transferts fédéraux sortants de scolarité, ligne 32700

Source : [annexe 11 Québec 2025, lignes 21–25 et instructions de désignation](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
Après l'utilisation obligatoire des reports antérieurs puis des frais courants
calculée par 5F, le maximum transférable est
`max(min(frais 2025 nets du CCF, 5000) - frais 2025 utilisés, 0)`.
Les reports antérieurs ne sont jamais transférables. Le montant désigné à
32700 peut être inférieur au maximum : il provient de l'autorisation signée
sur le certificat, et non d'un crédit calculé saisi manuellement. Tout
montant supérieur au maximum est refusé. Le report futur est réduit du
transfert, sans ajouter de crédit au dossier de l'étudiant ni modifier
32300, les revenus ou le calcul Québec.

Un bénéficiaire unique est identifié : conjoint, parent ou grand-parent de
l'étudiant ou de son conjoint. Pour un parent/grand-parent, confirmation
explicite que le conjoint ne réclame pas 30300, 30425 ou 32600 pour l'étudiant.
Source, autorisation signée, lien et unicité sont validés par le comptable;
le moteur ne détermine pas automatiquement l'admissibilité documentaire.

Ce bloc étend 5F aux transferts sortants fédéraux. Les transferts reçus dans
le dossier du bénéficiaire et les transferts Québec restent des fonctions
distinctes à livrer. Les autres limites 5F restent applicables. L'absence de
transfert des anciens profils ne peut pas être confirmée simultanément avec
un transfert sortant positif.

Le profil imbriqué `reports_federaux.transfert_sortant` conserve uniquement
les données de désignation et les confirmations. Ancien JSON sans ce profil :
profil vide. Types, clés inconnues, montants non finis, précision et plafonds
sont contrôlés; les résultats sont recalculés et les divergences entre profil
explicite et estimation sont refusées. GUI : choix du lien et données du
certificat, révocation des confirmations après modification. Trace et PDF :
bénéficiaire, source, maximum, 32700 et report futur après transfert.

Validation ciblée : **201 passed, 5 warnings**, couvrant aussi CCF, reports,
ancien JSON, divergence, bornes, non-finis, GUI, trace et PDF. Aucun test
existant modifié.

Suite complète 5G : **3947 passed, 8 warnings** (`--capture=sys`).


### Bloc 5H livré — scolarité reçue d'enfants ou petits-enfants, ligne 32400

Sources 2025 : [ARC, ligne 32400](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-32400-tuition-education-textbook-amounts-transferred-a-child.html)
et [annexe 11, lignes 21–24](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s11/5005-s11-25e.pdf).
Le bénéficiaire peut recevoir des désignations de plusieurs étudiants; chaque
étudiant désigne un seul bénéficiaire. Ce dernier doit être un parent ou
grand-parent admissible de l'étudiant ou de son conjoint. Le conjoint de
l'étudiant ne doit pas réclamer 30300, 30425 ou 32600 pour cet étudiant.

La donnée saisie est le montant désigné sur le certificat signé. Le comptable
vérifie la déclaration de l'étudiant, l'annexe 11, la concordance avec 32700,
les frais courants nets du CCF, leur utilisation personnelle et le plafond
`max(min(frais courants nets, 5000) - frais courants utilisés, 0)`.
Aucun report antérieur ne peut être transféré. Ce profil bénéficiaire ne
reconstitue pas automatiquement la déclaration du tiers : il exige ces
confirmations et la source documentaire. Il vérifie en plus la borne absolue
de 5000 $ par étudiant, les cents, les montants finis, le lien et les doublons
de références d'étudiants. Il n'impose pas de plafond global de 5000 $.

32400 additionne les désignations et entre une seule fois dans 33500, après
le calcul de la scolarité personnelle. 33800, 34990 et 35000 sont recalculés;
le crédit est non remboursable. Aucun solde n'est reporté chez le bénéficiaire.
Revenus et impôt Québec inchangés. Les reports personnels 5F et transferts
sortants 5G peuvent coexister : leurs montants ne comprennent jamais 32400.
Les libellés de leurs confirmations distinguent désormais les frais personnels
des désignations reçues. Le transfert reçu du conjoint, 32600 / annexe 2,
est traité séparément par 5K. Les transferts Québec restent à livrer.

Le JSON persiste uniquement les désignations et confirmations dans
`transferts_scolarite_recus`; ancien JSON sans ce champ = profil vide.
Clés inconnues, types et confirmations invalides sont refusés au chargement;
un profil explicite divergent de l'estimation est refusé à la sauvegarde.
Les références locales d'étudiants permettent de distinguer les dossiers
sans demander de NAS. L'unicité réelle et le lien restent à vérifier sur pièces.

GUI : liste de plusieurs étudiants, ajout, modification, retrait, réouverture;
modification des données = révocation des confirmations. Une saisie modifiée
non enregistrée empêche l'application du profil. Trace et PDF indiquent chaque
étudiant, sa référence, sa source, sa désignation et le total 32400.

Validation ciblée : **203 passed, 5 warnings**, incluant scolarité existante,
stockage, GUI, trace, PDF, compensation 34990 et combinaison 5F/5G.
Aucun test existant modifié.

Suite complète 5H : **4014 passed, 8 warnings** (`--capture=sys`).


### Correctif — valeurs non finies dans les dons et leurs revenus de calcul

Le validateur de dons acceptait `Infinity`, des flottants et des booléens;
`NaN` et certains types déclenchaient des exceptions techniques avant le
message de validation. Les fonctions de crédit acceptaient aussi des types
incorrects pour le revenu imposable.

Les deux montants de dons et les deux revenus de calcul doivent maintenant
être des `Decimal` finis avant toute comparaison. Les taux, plafonds,
confirmations et arrondis existants ne changent pas. Les fractions de cent
finies déjà acceptées restent arrondies au calcul du crédit. Il s'agit d'un
contrôle de données, sans nouvelle règle d'admissibilité fiscale.

Régression avant correctif : **32 failed, 1 passed**. Après correctif et
non-régression ciblée : **200 passed, 5 warnings**. Aucun test existant modifié.
Une exécution sandbox avait échoué à préparer `tmp_path` (accès refusé);
la relance hors sandbox utilise les mêmes tests, sans contournement métier.

Suite complète du correctif : **4047 passed, 8 warnings** (`--capture=sys`).


### Bloc 5I livré — reports fédéraux de dons monétaires et choix de réclamation

Sources 2025 : [ARC, montant des dons à réclamer et reports](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-34900-donations-gifts/how-much-claim.html)
et [annexe 9, lignes 6–10 et 20–23](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.pdf).
Les dons monétaires ordinaires inutilisés des cinq années précédentes sont
admissibles au report : banques 2020–2024 pour une réclamation en 2025.
Les dons antérieurs doivent être utilisés avant ceux de 2025. Le logiciel
les répartit des plus anciens aux plus récents afin de limiter l'expiration;
cet ordre entre années antérieures est un choix logiciel documenté.

Le contribuable choisit le montant de dons à réclamer, y compris zéro ou une
partie seulement. Ce choix n'est pas un crédit calculé. Le moteur refuse un
choix dépassant les dons disponibles ou 75 % du revenu net 23600 après
les déductions. Les dons 2025 bruts restent conservés même s'ils dépassent ce
plafond. Chaque année est ventilée entre utilisation et solde; le reliquat
2020 expire après 2025 et n'entre pas dans les reports futurs. Les autres
reliquats conservent leur année d'origine et leur dernière année de réclamation.
Aucune optimisation automatique du choix ou de l'impôt restant n'est annoncée.

Le profil `dons_bienfaisance.reports_federaux` s'active explicitement.
Source par année, reçus, montants non déjà réclamés, choix et validation
comptable sont obligatoires. Le garde-fou janvier/février 2025 déjà réclamé
en 2024 reste actif. Aucun décès, don en nature, écologique/culturel,
régime américain, abri fiscal ou report Québec dans 5I. Les taux supérieurs
33 % fédéral et 25,75 % Québec sont désormais calculés par 5J.
Sans activation, le comportement antérieur reste inchangé.

34900 et la part des premiers 200 $ de l'annexe 9 ligne 22 utilisent uniquement
les dons choisis pour la réclamation. 34990 puis 35000 sont recalculés, sans
double crédit. Les revenus et le crédit Québec ne sont pas modifiés par les
reports fédéraux. Les dossiers avec seulement des dons antérieurs sont admis.

JSON : entrées et confirmations seulement, montants décimaux sérialisés en
chaînes; ancien JSON sans profil = profil vide. Clés, types, années en double,
montants non finis et précision invalides sont refusés. Résultats reconstruits,
divergence entre profil explicite et estimation refusée. GUI : choix et cinq
soldes annuels avec sources dans les ajustements fiscaux; changement des dons
courants ou des reports = révocation des confirmations. Trace/PDF détaillent
plafond, choix, utilisation par année, reports futurs, expiration et 34900.

Validation ciblée : **249 passed, 5 warnings**, incluant ancien JSON, report
seul, REER réduisant le plafond, 34990, janvier/février, GUI, stockage, trace,
PDF et formulaire CELIAPP partagé. Aucun test existant modifié.

Suite complète 5I : **4128 passed, 8 warnings** (`--capture=sys`).


### Bloc 5J livré — taux supérieurs des crédits pour dons et hauts revenus

Sources 2025 : [annexe 9 fédérale, lignes 13–23](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s9/5000-s9-25e.pdf)
et [grille Québec 395, page 2, lignes 1–12](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.GR%282025-12%29.pdf).
Au fédéral : 14,5 % sur les premiers 200 $; 33 % sur le minimum entre
l'excédent des dons réclamés sur 200 $ et l'excédent du revenu imposable 26000
sur 253 414 $; 29 % sur le reste. Au Québec : 20 % sur les premiers 200 $;
25,75 % sur le minimum entre l'excédent des dons sur 200 $ et l'excédent du
revenu imposable 299 sur 129 590 $; 24 % sur le reste. Les excédents de revenu
ont un plancher zéro. Chaque composante monétaire est arrondie au cent avant
addition, selon les lignes des formulaires.

Les anciens refus fondés uniquement sur ces seuils de revenu sont supprimés,
y compris lorsque les dons sont nuls. Les mentions historiques de ces refus
dans les anciens blocs sont supersédées par 5J. Les autres validations,
le plafond fédéral de 75 %, les reports 5I et les exclusions de dons
spécialisés restent applicables. Les reports Québec restent à livrer en
priorité 6; aucune règle fédérale n'est transposée au Québec.

La base fédérale provient de la réclamation choisie en 5I lorsque ce profil
est actif. La part de l'annexe 9 ligne 22 demeure limitée aux premiers 200 $,
sans inclure les crédits à 29 % ou 33 % dans la compensation 34990.
Les estimations recalculent 34900, 35000 et l'abattement normalement.
Les ventilations sont immuables et dérivées; aucun nouveau champ JSON ou
montant à saisir dans la GUI. Trace et PDF exposent les bases par taux,
les revenus/seuils utilisés et les crédits 34900/395. Le PDF détaille aussi
les dons ordinaires sans report, auparavant absents de sa section dédiée.

Validation ciblée : **430 passed, 5 warnings**. Les anciens tests exigeant
le refus des hauts revenus sont remplacés par des résultats fiscaux précis.
Les tests FSS/intérêts, RRQ/RPC et PSV vérifient désormais l'estimation complète
au-delà de 129 590 $, y compris la récupération PSV, au lieu du refus antérieur.
La trace vérifie les six nouvelles bases par taux et leurs montants exacts.
Ces changements correspondent à la
nouvelle fonctionnalité; aucun test n'est supprimé, ignoré ou affaibli pour
masquer une régression. Les nouveaux tests couvrent les seuils au cent près,
les trois composantes, les arrondis, l'absence de dons, les reports, la trace
et les limites de page PDF.

Suite complète 5J : **4148 passed, 8 warnings** (`--capture=sys`).

### Correctif — revenus finis du montant pour conjoint 30300

L'audit préalable aux transferts familiaux a reproduit un défaut de validation :
un revenu du contribuable `Infinity` pouvait produire un montant 30300,
et `NaN` provoquait une erreur `InvalidOperation`. Les deux revenus du profil
30300 exigent désormais des `Decimal` finis avant comparaison ou calcul,
y compris lorsque le profil est inactif. Les types incorrects produisent une
`ValueError` explicite. Les contrôles des négatifs et la formule restent inchangés.

La [référence ARC 30300 pour 2025](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-30300-montant-epoux-conjoint-fait.html)
reste la base fiscale; ce correctif porte sur la validité numérique des entrées,
sans élargissement des situations familiales admises. Aucun changement de schéma
JSON ou de saisie GUI. Les données finies existantes conservent leur résultat.

Régression reproduite avant correction : **36 failed, 1 passed**.
Validation ciblée après correction : **133 passed, 5 warnings**, incluant
calculs 30300, profils inactifs, intégration, compensation et stockage.

Suite complète après correctif : **4185 passed, 8 warnings** (`--capture=sys`).

### Bloc 5K livré — transferts fédéraux du conjoint, ligne 32600

Sources 2025 : [annexe 2 Québec 5005-S2](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s2/5005-s2-lp-25e.pdf)
et [T1 Québec 5005-R, pages 5–6](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.pdf).
L'annexe additionne les montants personnels du conjoint 30100, 30500, 31400
(maximum 2 000 $), 31600 et sa scolarité courante désignée au bénéficiaire.
Elle soustrait le revenu imposable ajusté : maximum zéro de l'équivalent
imposable moins 30000, la ligne 100 de la T1 Québec et 32300.
L'équivalent est 26000 jusqu'à 57 375 $; au-delà, il est l'impôt brut de la
ligne 77 divisé par 14,5 %, arrondi au cent. La ligne 32600 est le solde
positif. La ligne 100 additionne les lignes T1 87–99 : elle n'inclut ni
31900, ni les montants familiaux, ni les frais médicaux, ni les dons.
Le calcul ne confond pas cette base avec la ligne 105 de l'annexe 11.

Le logiciel importe un instantané des **entrées** du dossier du conjoint
et les recalcule avec le même moteur. Il retire le résumé d'estimation et
le chemin du PDF. Aucun montant de crédit dérivé n'est saisi. L'import ne
lit pas les pièces sources et ne dépend pas du maintien du fichier original.
Après une correction chez le conjoint, il faut réimporter puis confirmer.
Les profils personnels et leurs confirmations d'absence de transfert décrivent
le calcul **avant** le nouveau transfert; l'autorisation 5K constitue une étape
distincte, avec vérification des deux dossiers et de l'unicité par le comptable.
Le moteur ne détermine pas automatiquement l'admissibilité détaillée du couple.

Le nom du bénéficiaire est conservé dans l'autorisation et comparé au dossier
courant. Deux personnes distinctes sont requises. Les revenus déclarés pour
30300 sont rapprochés des revenus recalculés; deux demandes 30300 simultanées
sont refusées. Une désignation de scolarité doit viser ce même conjoint et
respecter le maximum recalculé par 5G. Les reports antérieurs de scolarité ne
sont pas transférés. Le même conjoint ne peut être inscrit à la fois à 32400
et à 32600. La base est ajoutée une seule fois à 33500, après la scolarité
personnelle; 33800, 34990, 35000 et l'abattement sont recalculés. Aucun revenu
ou crédit Québec n'est modifié par ce transfert fédéral.

Périmètre logiciel actuel : deux dossiers 2025 résidents du Canada toute
l'année et du Québec en fin d'année, sans décès/faillite ni traitement
spécialisé omis. L'absence de rupture pendant au moins 90 jours comprenant
le 31 décembre doit être confirmée selon l'annexe 2. Les transferts 32600
imbriqués/réciproques, les doubles montants 30500 sans fiches identifiées
(enfants distincts désormais couverts par 5AB) et les combinaisons avec les profils individuels ACT ou
supplément médical restent refusés. Ces limites logicielles ne constituent
pas des exclusions fiscales générales. Les autres limites du moteur restent
appliquées aux deux dossiers. Les combinaisons familiales plus générales
restent à poursuivre dans la roadmap.

JSON rétrocompatible : profil absent = profil vide; champs et booléens nouveaux
validés strictement; profil explicite différent de l'estimation refusé.
Seuls l'instantané brut, le bénéficiaire, la source et les confirmations sont
persistés. GUI : import, aperçu calculé en lecture seule, application et retrait;
import ou modification de source révoque les confirmations. Trace et PDF montrent
les lignes de l'annexe 2, les réductions, les sources et le résultat 32600.

Validation ciblée : **240 passed, 5 warnings**. Aucun test existant modifié.

Suite complète 5K : **4252 passed, 8 warnings** (`--capture=sys`).

### Bloc 5L livré — pompiers volontaires et recherche-sauvetage, 31220 / 31240

Sources officielles : [ARC, lignes 31220 et 31240, année 2025](https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/sujets/tout-votre-declaration-revenus/declaration-revenus/remplir-declaration-revenus/deductions-credits-depenses/ligne-31220-montant-pompiers-volontaires-ligne-31240-montant-volontaires-recherche-sauvetage.html)
et [ARC, revenu exonéré des volontaires, ligne 10105](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-income/line-10100-employment-income/tax-exempt-income-for-emergency-services-volunteers.html).
Le montant admissible est **6 000 $**, sur une seule des lignes 31220 ou 31240.
Il faut au moins 200 heures admissibles combinées de services de pompier
volontaire et de recherche-sauvetage, avec des services dans l'activité choisie.
Les heures auprès d'un organisme où des services similaires sont également
rémunérés sont exclues; l'admissibilité du service ou de l'organisme doit être
vérifiée. Les heures proviennent des certificats du chef, de son délégué ou
du responsable compétent; le moteur ne classe pas automatiquement les tâches
ni ne détermine l'admissibilité détaillée des heures.

Le choix fiscal est explicite : `exoneration`, `pompiers` ou `sauvetage`.
La case 87 du T4 est extraite, validée sur pièces et rapprochée de la case 14
du même document. Une case 87 positive sans choix est refusée. Montants non
finis, négatifs, hors cents, supérieurs à 1 000 $ par employeur admissible,
doublons, documents absents et valeurs non validées sont refusés.
Avec l'exonération, la case 87 va à 10105 et aucun crédit n'est appliqué.
Avec un crédit, toutes les cases 87 sont ajoutées une seule fois aux revenus
d'emploi 10100 et 10105 est nul : aucun double avantage.

La réintégration précède les calculs de revenu net, plafonds, réductions et
crédits. Elle alimente aussi les revenus utilisés pour l'ACT et le supplément
médical. Les gains assurables/admissibles et retenues restent ceux des feuillets
validés; ce bloc ne reconstitue pas une paie ni une nouvelle assujettissabilité.
La base 31220/31240 entre dans 33500 **avant** la scolarité personnelle;
33800, 34990, 35000 et l'abattement sont recalculés. Le dossier du conjoint
5K reprend ces lignes dans sa base T1 Québec ligne 100. Aucun revenu, crédit
ou exonération Québec n'est déduit de la règle fédérale.

Le profil `benevoles` conserve le choix, la source, les activités par organisme,
les heures et leurs certificats ainsi que les confirmations. Les calculs dérivés
et montants des cases 87 ne sont pas dupliqués dans ce profil : les cases restent
dans les données fiscales validées. Ancien JSON sans profil = profil vide;
clés inconnues, types invalides et divergences profil/estimation sont refusés.
Les anciens dossiers sans ce bloc restent chargeables, y compris d'autres années.

GUI : choix fiscal, liste d'activités, ajout/modification/retrait, contrôles
d'organisme et de rémunération, confirmations puis application ou effacement.
Toute modification du choix, de la source ou d'une activité révoque les
confirmations. Aucun crédit calculé n'est saisi. Trace et PDF montrent les
heures retenues/exclues, sources, case 87, réintégration 10100, exemption 10105
et base du crédit. Le revenu fédéral de la trace identifie désormais les
cases 14 **et** 87 lorsque la réintégration est appliquée.

Périmètre : règles des organismes et certificats vérifiées par le comptable;
profils d'emploi et combinaisons déjà admis par le moteur. Le garde-fou général
d'un T4 et d'un RL-1 demeure; les employeurs multiples relèvent de la priorité 7.
Le crédit Québec des volontaires reste à traiter séparément en priorité 6.

Validation ciblée : **332 passed, 5 warnings**, incluant seuil 199,99/200/200,01,
services exclus, choix exclusifs, données invalides, extraction, stockage ancien,
GUI, scolarité, ACT, transfert conjoint, trace et PDF. Aucun test existant modifié.

Suite complète 5L : **4321 passed, 8 warnings** (`--capture=sys`).

### Bloc 5M livré — frais d'adoption fédéraux, ligne 31300

Sources : [ARC, ligne 31300, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-31300-adoption-expenses.html),
[LIR 118.01](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/page-89.html)
et [T1 Québec 2025, page 6](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.pdf).

La période commence à la première demande d'inscription au ministère/agence
agréée ou à la cour canadienne, et finit à la dernière des dates d'ordonnance
reconnue au Canada et de résidence permanente avec le demandeur. Sa fin doit
être en 2025; l'enfant doit avoir moins de 18 ans à l'ordonnance. Les dépenses
payées, engagées pendant cette période, peuvent concerner plusieurs années.
Catégories : agence, frais judiciaires/juridiques/administratifs, voyage/séjour
raisonnable et nécessaire, traduction, institution étrangère obligatoire,
immigration obligatoire et autres frais obligatoires admissibles.

Par enfant : frais moins aides reçues ou à recevoir par quiconque, plancher zéro,
puis plafond **19 580 $**, puis part convenue du demandeur. LIR 118.01(2) exclut
de la réduction les aides déjà incluses au revenu du demandeur et non déductibles
de son revenu imposable. Ce traitement doit être justifié sur pièces; le bloc
ne crée pas une inclusion au revenu. Le solde maximal des autres demandeurs
est présenté pour contrôler le partage, y compris les arrondis au cent.

Le moteur vérifie dates, âge, références dupliquées, Decimal finis non négatifs,
cents et pourcentages. Il ne détermine pas l'admissibilité détaillée : organismes,
caractère raisonnable/obligatoire, paiements, aides et partage exigent une validation
comptable explicite. Les sources identifient chaque facture ou portion ventilée.
Une même référence réutilisée est refusée; les portions distinctes d'une facture
commune doivent avoir des références distinctes et un total vérifié.

31300 entre une seule fois dans 33500 avant la scolarité personnelle. 33800,
34990, 35000 et l'abattement sont recalculés; les revenus et le calcul Québec
restent inchangés. L'annexe 2 du conjoint reprend 31300 dans sa ligne 100.
Quand son dossier brut est importé par 5K, les demandes pour le même enfant
(nom normalisé et date de naissance) sont rapprochées du maximum commun.
Sans ce dossier, le partage reste une validation sur pièces; aucune autre
déclaration n'est recherchée automatiquement. Le crédit Québec est distinct
et reste à traiter en priorité 6.

JSON : seules les données brutes, sources et confirmations sont enregistrées;
ancien profil absent = vide. Champs inconnus, types invalides et divergence
profil/estimation sont refusés. Les résultats sont recalculés au chargement
et lors de l'estimation. GUI : enfants et dépenses ajoutables, modifiables et
retirables, part convenue saisie en pourcentage, aucun crédit calculé saisi.
Les modifications révoquent les confirmations; une dépense non enregistrée
bloque l'application. Trace et PDF détaillent période, frais, aides, plafond,
partage, sources et total 31300.

Validation ciblée : **291 passed, 5 warnings**. Aucun test existant modifié.

Suite complète 5M : **4425 passed, 8 warnings** (`--capture=sys`).
Rendu du rapport PDF synthétique vérifié visuellement.

### Bloc 5N livré — contributions politiques fédérales, 40900 / 41000

Sources : [ARC, crédit politique, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/federal-political-contributions-line-40900-total-contributions-line-41000-tax-credit.html),
[feuille fédérale 2025, page 8](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf),
[LIR 127(3), (3.1) et (4.1)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/page-109.html),
[T1 Québec 2025, pages 7 et 8](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.pdf).

Les paiements monétaires de 2025 à un parti fédéral enregistré, une association
enregistrée ou un candidat fédéral sont saisis par reçu officiel. Le donateur,
le bénéficiaire, la date, le paiement, les avantages reçus ou attendus et la
référence sont conservés. Les reçus du conjoint peuvent être réclamés si ce
dernier ne les réclame pas. Le comptable vérifie l'admissibilité, l'autorisation
du signataire, la concordance du montant net avec les reçus et l'absence de
double demande, notamment parmi les dons de bienfaisance.

40900 = paiements moins avantages. 41000 = 75 % des premiers 400 $, puis 50 %
des 350 $ suivants, puis **un tiers** de l'excédent, maximum **650 $**.
Le moteur conserve le taux exact prévu par 127(3), puis arrondit au cent;
la feuille papier affiche le troisième taux arrondi à 33,33 %. Ce choix de
précision est explicite et testé aux seuils, dont 1 274,99 / 1 275 $.
Les contributions en nature et les exclusions de 127(4.1), dont certains
avantages financiers publics et paiements en qualité d'agent, ne sont pas admises.
Le profil demande confirmation de leur absence.

Le crédit est appliqué après 40500 : dans ce profil, 41600 contient 41000,
puis 41700 = max(40600 - 41600, 0). Les avances ACT 41500 sont ajoutées ensuite.
L'inutilisé est montré, sans remboursement ni report propre à ce crédit.
Les bases 33500, 33800, 34990, 35000 et 42900 restent inchangées, tout comme
44000 = 16,5 % de 42900. L'abattement demeure remboursable même si 41700 est nul.
Aucun revenu ou crédit Québec n'est modifié. Le crédit politique n'entre pas
dans les montants transférables de l'annexe 2.

Périmètre logiciel : reçus personnels monétaires; les attributions T5003/T5013
de sociétés de personnes restent à traiter avec les profils avancés. Les
contributions du conjoint combinées aux profils actuellement individuels ACT
ou supplément médical sont refusées en attendant leur extension familiale.
Ces restrictions logicielles ne sont pas des exclusions fiscales générales.
Avec un dossier conjoint importé par 5K, les identités et références des reçus
réclamés sont rapprochées pour refuser une double demande connue. Sans dossier
importé, le choix du conjoint est validé sur pièces, sans recherche externe.

Stockage rétrocompatible : profil absent = vide; seuls reçus, sources et
confirmations sont persistés. Clés inconnues, types invalides, dates hors 2025,
Decimal non finis/négatifs/hors cents et profils explicites divergents sont
refusés. GUI : ajout, modification, retrait des reçus, confirmation du choix;
les modifications révoquent les validations et aucun crédit calculé n'est saisi.
Trace, résumé et PDF montrent les contributions, avantages, formule, crédit
utilisé/inutilisé et ordre 40500 → 41000/41600 → 41700 → 41500, avec 44000 séparé.

Validation ciblée : **330 passed, 5 warnings**. Aucun test existant modifié.

Suite complète 5N : **4537 passed, 8 warnings** (`--capture=sys`).
Rapport PDF synthétique vérifié visuellement.


### Bloc 5O livré — fonds de travailleurs fédéraux, 41300 / 41400

Sources : [ARC, fonds de travailleurs, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/lines-413-414-labour-sponsored-funds-tax-credit.html),
[LIR 127.4, notamment (1), (5) et (6)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-127.4.html),
[T1 Québec 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-r/5005-r-25e.pdf),
[RQ, ligne 424 pour 2025](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/400-a-447-impot-et-cotisations/ligne-424/),
[relevé 10 officiel](https://www.revenuquebec.ca/documents/fr/formulaires/rl/RL-10(2025-10).pdf).

Périmètre : acquisitions initiales FTQ catégorie A ou Fondaction A/B,
directes, par REER personnel ou conjoint, ou par CELI propre suivant la
fiducie admissible définie par 127.4(1). Souscription irrévocable payée et
premier détenteur sont vérifiés sur pièces. Pour le REER conjoint, souscripteur
et rentier sont identifiés; une même action ne peut être partagée entre eux.
Les SCRT uniquement agréées au fédéral ne sont pas admissibles en 2025.
Les autres fonds provinciaux ne sont pas couverts par ce profil Québec.

Coût net = prix payé moins aides publiques reçues ou attendues, sans soustraire
les crédits d'impôt. Dates admises : 1 janvier 2025 au 2 mars 2026 inclusivement.
Pour début 2026, le choix de coût réservé à 2026 est exclu de 41300 en 2025.
Pour les acquisitions du 1 janvier au 1 mars 2025, le crédit effectivement
déduit en 2024 est une donnée historique documentée, non un nouveau crédit
calculé saisi manuellement. Il est retranché du potentiel de 15 % **avant** le
plafond de 750 $, conformément à 127.4(5). Exemple : coût net 10 000 $,
crédit utilisé en 2024 de 750 $ → min(750, 1 500 - 750) = 750 $ pour 2025.
La ligne 41300 conserve le coût net des acquisitions considérées; la trace
sépare l'utilisation historique. Le taux est 15 %, distinct du taux général
2025 de 14,5 %. Aucun report fédéral général n'est créé; les acquisitions de
début 2026 peuvent nécessiter un examen de leur solde dans la déclaration 2026.

L'admissibilité provinciale des actions conditionne le crédit fédéral.
Les dates de naissance, rentes de retraite, congés payés sans retour prévu,
revenus d'emploi/entreprise et demandes de rachat sont explicites. Les personnes
nées avant 1961 sont exclues. Pour celles nées avant 1981, retraite/préretraite
exclut le crédit, sauf l'exception des revenus de travail supérieurs à 3 500 $
avec les autres conditions RQ. Les sommes de régime reçues en raison du décès
du conjoint ne sont pas assimilées aux rentes visées. Les deux personnes sont
contrôlées pour un REER conjoint. Le revenu de travail du contribuable doit
concorder avec le revenu d'emploi Québec du dossier; les revenus autonomes
attendent la priorité 7. Les autres faits et pièces demeurent soumis à la
validation comptable, sans détermination automatique complète d'admissibilité.

Restrictions logicielles explicites : échanges, rachats et annulations,
remplacements RAP/REEP, remboursement 211.9, décès et décisions ministérielles
d'acquisition réputée ne sont pas couverts. Toute demande de rachat déclenche
un refus conservateur du profil, même lorsqu'un traitement fiscal spécialisé
pourrait permettre un crédit. Ce refus n'est pas une exclusion fiscale générale.
Le calcul Québec 424, ses reports et ses annulations restent distincts et
seront traités en priorité 6. Aucune déduction REER n'est créée automatiquement.

Ordre : 40500 puis 41000 puis 41400; 41600 = 41000 + 41400 dans ce profil.
41700 = max(40600 - 41600, 0), puis ajout des avances ACT 41500. Les crédits
utilisés sont ventilés sans double consommation. 33500/33800/34990/35000,
42900, revenu et impôt Québec restent inchangés. L'abattement remboursable
44000 reste 16,5 % de 42900. Le profil conjoint reste refusé avec ACT ou
supplément médical tant que leur extension familiale n'est pas développée.
Les références d'acquisitions communes aux deux dossiers importés par 5K
sont refusées; hors import, l'absence de double demande est validée sur pièces.

JSON rétrocompatible : absence du profil = vide; seules acquisitions,
situations, choix, pièces historiques et confirmations sont enregistrés.
Les résultats sont reconstruits. Clés inconnues, mauvais types, montants
non finis/négatifs/hors cents, dates et profils explicites divergents sont
refusés. GUI : ajout/modification/retrait des acquisitions, historique 2024,
choix 2026, situations des personnes; modification révoquant les confirmations.
Aucun crédit 2025 calculé n'est saisi. Résumé, trace et PDF détaillent sources,
aides, historique, plafond, utilisation effective et ordre fiscal.

Validation ciblée : **399 passed, 5 warnings**. Aucun test existant modifié.

Suite complète 5O : **4692 passed, 8 warnings** (`--capture=sys`).
Rapport PDF synthétique vérifié visuellement.

### Bloc 5P livré — fournitures scolaires d'éducateur, 46800 / 46900

Sources : [ARC, fournitures scolaires, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/lines-46800-46900-eligible-educator-school-supply-tax-credit.html),
[LIR 122.9](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.9.html),
[RIR 9600, biens durables prescrits](https://laws-lois.justice.gc.ca/eng/regulations/C.R.C.%2C_c._945/section-9600.html).
Les dernières modifications des dispositions consultées datent de 2022;
la page ARC confirme leur application à 2025.

Crédit fédéral **remboursable** : 46800 = min(1 000 $, dépenses admissibles),
puis 46900 = 25 % de 46800, maximum 250 $. Ajout unique aux paiements du
rapprochement, même en l'absence d'impôt. Aucun revenu, crédit non remboursable,
33500/33800/34990/35000, base 42900 ou abattement Québec n'est modifié.
Ce bloc ne crée aucun crédit provincial.

Employeur, province/territoire d'emploi et qualification reconnue sont
documentés. Le comptable confirme l'emploi au Canada en 2025 comme enseignant
ou éducateur à la petite enfance dans une école primaire/secondaire ou une
garderie réglementée, avec certificat, permis ou diplôme valide et reconnu.
Le logiciel ne détermine pas seul cette admissibilité.

Chaque achat personnel payé en 2025 conserve date, description, catégorie,
prix de la portion professionnelle, aides reçues ou auxquelles l'éducateur
a droit, portion d'aide imposable non déductible et référence unique de pièce.
L'usage personnel est exclu avant saisie et sa ventilation est validée.
La portion financée par une aide est retranchée, sauf l'exception légale des
aides incluses au revenu et non déductibles du revenu imposable. Aucun montant
ne doit avoir servi à une autre déduction fédérale de revenu ou d'impôt pour
quiconque, quelle que soit l'année. Avec une déduction T777, une source de
rapprochement distinct des fournitures est obligatoire. Le bloc 4C contient
des agrégats : le rapprochement des factures reste humain et documenté,
sans détection automatique exhaustive des dépenses déjà déduites.

Catégories : consommables et liste fermée du RIR 9600 — livres, jeux et
casse-têtes, contenants, logiciels éducatifs, calculatrices, stockage externe,
webcams/microphones/casques, projecteurs, pointeurs sans fil, jouets éducatifs
électroniques, minuteries numériques, haut-parleurs, diffusion vidéo,
imprimantes et ordinateurs/tablettes. Ces derniers sont refusés si l'employeur
met un ordinateur ou une tablette à disposition pour utilisation hors classe.
L'usage professionnel et la classification sont vérifiés sur pièces.

L'attestation écrite de l'employeur n'est pas une exigence universelle
préalable. Si l'ARC l'a demandée et qu'elle n'est pas fournie, le crédit est
nul selon 122.9(2)c), avec motif dans le rapport. Le statut fourni exige une
référence. Résidence partielle, non-résidence, faillite et déclarations
spéciales de décès restent des limites logicielles à traiter en priorité 7,
et non des exclusions fiscales générales.

JSON rétrocompatible : profil absent = vide; achats, choix, faits, sources
et confirmations seuls sont enregistrés; résultats reconstruits. Clés
inconnues, types invalides, Decimal non finis/négatifs/hors cents, dates hors
2025 et divergences profil explicite/estimation sont refusés. GUI : ajout,
modification, retrait et effacement; modification révoquant les confirmations.
Aucun crédit calculé saisi manuellement. Trace, résumé et PDF présentent
dépenses nettes, aides, plafond, statut d'attestation, 46800/46900 et résultat.

Validation ciblée : **281 passed, 5 warnings**. Aucun test existant affaibli.

Suite complète 5P : **4831 passed, 8 warnings** (`--capture=sys`).
Rapport PDF synthétique vérifié visuellement.

### Bloc 5Q livré — rénovation multigénérationnelle, 45354 / 45355

Sources normatives : [annexe 12 fédérale 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s12/5000-s12-25e.pdf),
[LIR 122.92](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.92.html),
[L.C. 2022, ch. 19, article 19(2)](https://laws-lois.justice.gc.ca/eng/AnnualStatutes/2022_19/FullText.html).
La disposition d'application et l'annexe 12 confirment la date de début
de 2023; la date de 2024 figurant sur la page explicative des dépenses ARC
consultée n'est pas retenue. Les dernières modifications de 122.92 datent
de 2024; le taux est celui du formulaire **2025**, soit **14,5 %**.

Pour chaque rénovation terminée en 2025, le moteur retient le moindre des
dépenses personnelles nettes d'aides et de 50 000 $ moins les bases réclamées
par les autres particuliers admissibles. Les bases sont additionnées à
45354; 45355 est calculée à 14,5 %, arrondie après cette addition.
Le plafond est propre à la rénovation, même si plusieurs particuliers
déterminés occupent le même logement secondaire. Plusieurs rénovations
distinctes pour des particuliers déterminés distincts sont possibles.
Le crédit remboursable est ajouté une seule fois aux paiements, sans
modifier les revenus, les crédits non remboursables ni l'abattement Québec.

Le particulier déterminé doit avoir 65 ans à la fin de 2025, ou au moins
18 ans et être admissible au CIPH. Son proche occupant doit être adulte
et avoir un lien familial énuméré avec lui ou son conjoint. Les rôles du
demandeur, la propriété canadienne, l'occupation attendue sous 12 mois,
la conformité du nouveau logement secondaire et l'historique d'une seule
rénovation à vie exigent des pièces et une validation comptable explicite.
Le logiciel ne détermine pas automatiquement cette admissibilité.

Les dépenses gardent fournisseur, description, date de pièce/contrat,
date du bien/service, date de paiement, montant, aides et source. Les
biens/services et paiements doivent être postérieurs à 2022; l'engagement
doit précéder l'achèvement. Un paiement postérieur à l'achèvement n'est pas
rejeté pour ce seul motif. La réalité des dates et paiements est validée.
Un fournisseur lié exige une référence d'inscription TPS/TVH. Une
attribution de fiducie exige sa notification et sa ventilation documentées.
Entretien courant, appareils ménagers, divertissement, entretien extérieur,
financement, travail personnel et autres dépenses non admissibles sont
exclus avant saisie, sous contrôle comptable.

Les mêmes portions ne peuvent servir aux frais médicaux fédéraux ni à
l'accessibilité domiciliaire. Avec ces profils actifs, une référence de
rapprochement est obligatoire. Les factures externes ne sont pas rapprochées
automatiquement : les doublons connus sont refusés, la ventilation entre
dossiers reste contrôlée par le comptable. Les autres demandes conservent
leur base de dépenses et leur accord de partage, sans saisir un crédit calculé.

JSON : profil absent = vide; données brutes seules, reconstruction des
résultats, refus des clés inconnues, types invalides et montants non finis.
La divergence entre profil explicite et estimation est refusée.
Moteur, estimation, stockage, trace, PDF et interface sont raccordés.
La GUI propose l'ajout, la modification et le retrait de projets, de dépenses
et de parts d'autres demandeurs. Annuler conserve les données initiales;
modifier révoque les confirmations. Aucun crédit calculé n'est saisi.
Validation ciblée : **306 passed, 5 warnings**, complétée par un contrôle
de lisibilité des confirmations GUI : **1 passed, 5 warnings**.
Le rapport PDF synthétique a été vérifié visuellement.
Suite complète : **4993 passed, 8 warnings** (`--capture=sys`), avant
l'ajout du contrôle de lisibilité précité; celui-ci passe séparément.
Faillite et décès restent des limites logicielles à traiter en priorité 7,
et non des exclusions générales de la loi.

### Bloc 5R livré — handicap fédéral détaillé et transfert 31800

Le montant personnel 31600 est de 10 138 $. Pour une personne de moins de
18 ans au 31 décembre 2025, le supplément est :
`max(5914 - max(soins - 3464, 0), 0)`.
Les soins comprennent les frais payés en 2025 pour la garde ou la surveillance,
réclamés par quiconque sous les articles 63, 64 ou 118.2, même dans une autre
année. Leur source, leur exhaustivité, l'approbation CIPH et l'absence de conflit
avec les soins spécialisés exigent une validation comptable. Le profil Québec
376 reste distinct; sa limite logicielle d'âge antérieure n'est pas levée.
Les anciens profils adultes restent compatibles sans les nouveaux champs.

**Calcul retenu pour 31800 : solde inutilisé selon LIR 118.3(2)d).**
Les entrées personnelles du donneur sont recalculées depuis un instantané JSON.
Soit `B` sa base 31600, supplément éventuel compris, et `I` son impôt fédéral
hypothétique avant les déductions de la division E autres que les articles
118 à 118.07 et 118.7. Les dons, dividendes, frais médicaux, scolarité, crédits
politiques et fonds ne créent donc pas artificiellement un transfert.
Le compensatoire 118(11) est recalculé sur les crédits permis dans cette
hypothèse; les ajouts pris en charge à l'impôt de la partie I sont inclus.

- Crédit DTC disponible : `C = arrondi_cent(B × 0,145)`.
- Crédit utilisé au sens de ce transfert : `U = min(C, I)`.
- Crédit inutilisé : `C - U`.
- Base transférable : `min(B, arrondi_cent((C - U) / 0,145))`.
- Base utilisée affichée : `B - base transférable`.
- Part du bénéficiaire : base transférable moins parts des autres soutiens,
  ou part moindre désignée par accord. La somme des parts ne peut dépasser
  la base disponible. Aucun montant transférable maximal n'est imposé par défaut.

La base utilisée est le complément au cent de la base transférable; elle
n'est pas une consigne de remplacer la ligne personnelle 31600 du donneur.
La distinction entre crédit d'impôt et base de crédit est conservée dans
les résultats, la trace et le PDF. Les arrondis peuvent créer quelques cents
d'écart de base avec une soustraction directe du revenu.

**Rapprochement de l'exemple 10 138 $ / 6 728,97 $.**
Le test d'intégration reconstruit un donneur adulte avec 80 000 $ de revenus
net et imposable, aucun supplément enfant, aucune part d'un autre soutien,
aucune demande concurrente 30400/32600 et un bénéficiaire satisfaisant aux
conditions hypothétiques 30450 documentées. Les crédits du donneur avant DTC
proviennent du montant personnel 16 129 $ et de 68 871 $ de frais d'adoption
pour quatre enfants : 19 580 + 19 580 + 19 580 + 10 131. Le total de base 102
est donc 85 000 $; aucun plafond individuel d'adoption n'est dépassé.

| Étape | Montant |
| --- | ---: |
| Impôt brut : 57375 × 14,5 % + 22625 × 20,5 % | 12 957,50 $ |
| Crédits permis : 85000 × 14,5 % | 12 325,00 $ |
| Compensatoire permis : (12325 - 8319,38) × 3,45 % | 138,19 $ |
| Impôt hypothétique avant DTC | 494,31 $ |
| Crédit DTC disponible | 1 470,01 $ |
| Crédit DTC utilisé | 494,31 $ |
| Crédit DTC inutilisé | 975,70 $ |
| Base DTC disponible - utilisée | 10138 - 3409,03 $ |
| Base inutilisée transférable | 6 728,97 $ |

La feuille fédérale 31800, page 6, lignes 8 à 13, donne réellement
`min(10138, max(10138 + 85000 - 80000, 0)) = 10138` pour ces mêmes entrées.
Le prototype ne reproduit pas cette soustraction : il applique le calcul
fondé sur l'impôt de 118.3(2)d), confirmé comme mécanisme par le folio 2.37.
La divergence exacte vient du barème progressif : la tranche de 22 625 $
supporte 6 points de plus que le taux des crédits, soit 1 357,50 $.
L'excédent de base de 5 000 $ ne compense que 725 $ d'impôt; après
compensatoire de 138,19 $, il reste 494,31 $. Les deux expressions ne sont
pas algébriquement équivalentes dans ce cas. Le calcul légal est retenu;
la documentation ne prétend pas que la feuille produit elle aussi 6 728,97 $.
Le total d'impôt réellement payable après tous les crédits ou remboursements
ne remplace pas l'impôt hypothétique expressément prévu pour le transfert.

**Admissibilité et garde-fous.** Le comptable vérifie le lien familial, le
soutien régulier pour les nécessités de la vie, les conditions 30400/30450,
l'autorisation, les obligations alimentaires et l'accord de partage. Les
lignes indiquées comme réellement réclamées sont contrôlées dans le dossier
bénéficiaire. Les demandes concurrentes du conjoint du donneur (dont 32600)
ou d'une autre personne à 30400 sont refusées; un réclamant 30400 ne partage
pas ce transfert. Le conjoint relève du bloc 32600 distinct. Les exceptions
alimentaires exigent les justificatifs et sont rapprochées de 22000.
Aucune admissibilité détaillée n'est inventée automatiquement.

**Limites logicielles.** Donneurs résidents du Québec et du Canada toute
l'année 2025, sans décès, faillite ou traitement spécial omis. Les instantanés
31800/32600 imbriqués sont refusés; le dossier importé précède les transferts.
Ces restrictions logicielles ne sont pas présentées comme des règles fiscales.

**Intégration.** 31800 entre une seule fois dans la base avant scolarité,
puis dans 33500/33800/34990. Revenus et calcul Québec sont inchangés.
Le JSON stocke les données brutes; anciens dossiers : profil vide. Les clés
inconnues et montants non finis sont refusés, les donneurs sont recalculés
au rechargement, les profils explicites divergents de l'estimation sont refusés.
La GUI gère import, donneurs, parts et désignations; une modification révoque
les confirmations. Trace et PDF présentent sources, calcul et parts par donneur.

Sources officielles consultées pour 2025 :
- [ARC, ligne 31800](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-31800-disability-amount-transferred-a-dependant.html).
- [RC4064 2025](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4064/disability-related-information.html).
- [DTC, montants 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/segments/tax-credits-deductions-persons-disabilities/disability-tax-credit/claiming-dtc.html).
- [Feuille fédérale 2025, pages 5 et 6](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).
- [LIR 118.3(2) et (3)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.3.html).
- [Compensatoire, LIR 118(11), applicable dès 2025](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.html).
- [Folio S1-F1-C2, paragraphes 2.30 à 2.37](https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index/series-1-individuals/folio-1-health-medical/income-tax-folio-s1-f1-c2-disability-tax-credit.html).

Validation : tests moteur, Decimal, bornes, supplément, transferts maximal,
partiel et nul, revenus nul/positif, partage, exclusions, JSON, estimation,
ordre avant scolarité, trace, PDF et GUI. Les tests de comparaison avec la
feuille conservent explicitement la divergence, sans affaiblir une assertion.
Dernière suite complète avant le complément d'audit : **5151 passed, 8 warnings**.
Complément moteur et intégration : **108 passed, 5 warnings**.
Validation ciblée finale du bloc : **172 passed, 5 warnings**.
Suite complète finale : **5159 passed, 8 warnings en 162,62 s**, avec
`--capture=sys`. Avertissements inchangés : cinq SWIG et trois openpyxl.
Revue visuelle du PDF actualisé : détail disponible/utilisé/inutilisé lisible.


### Audit après 5R — suites de la Priorité 5

L'inventaire d'ouverture de ce document est historique. Les blocs 5A à 5R
ont livré les crédits et transferts décrits plus bas. L'audit réel après
`ea0703b` relève encore : frais médicaux familiaux 33099/33199 (le profil
antérieur exige sans conjoint ni personne à charge), ACT familial,
supplément médical familial, et les combinaisons restantes de crédits
personnels à examiner dans l'orchestrateur. La Priorité 5 n'est pas clôturée.
Le prochain bloc est nommé 5S pour traiter le premier manque constaté;
les extensions familiales des prestations suivront avant l'audit de clôture.
Les crédits Québec et profils avancés restent aux Priorités 6 et 7.

### Bloc 5S — frais médicaux familiaux fédéraux, 33099 / 33199 / 33200

Sources officielles 2025 :
- [ARC, frais médicaux 33099 et 33199](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/lines-33099-33199-eligible-medical-expenses-you-claim-on-your-tax-return.html).
- [Feuille fédérale 2025, 33199](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).
- [LIR 118.2(1), groupes B et D, période commune](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.2.html).

Le profil détaillé distingue le demandeur, le conjoint, les enfants mineurs
au 31 décembre 2025 et les autres personnes à charge. Les petits-enfants
relèvent de 33199 même mineurs. Les liens admissibles, la dépendance,
l'admissibilité de chaque reçu et les interactions avec soins/handicap/garde
sont vérifiés par le comptable. Le moteur ne détermine pas automatiquement
l'admissibilité médicale. La résidence canadienne à un moment de l'année
est exigée pour les liens autres qu'enfant et petit-enfant à 33199.

Les reçus sont identifiés, datés, attribués à une personne et regroupés dans
une même fenêtre d'au plus douze mois se terminant en 2025. Une saisie de
période plus courte est incluse dans cette fenêtre, sans changer les reçus
retenus. Les remboursements reçus ou à recevoir sont soustraits, sauf leur
part imposable non déduite; les parts réclamées ailleurs sont aussi retirées.
L'absence de double demande entre dossiers ou années exige les pièces.
Les références dupliquées sont refusées à l'intérieur du profil.

- 33099 = somme des reçus nets du demandeur, conjoint et enfants mineurs.
- Net 33099 = max(33099 - min(3 % du revenu net du demandeur, 2834), 0).
- Pour chaque autre personne : max(frais nets - min(3 % de son revenu net, 2834), 0).
- 33199 = somme de ces résultats individuels; aucun solde négatif d'une personne
  ne réduit le montant positif d'une autre.
- 33200 = net 33099 + 33199; une seule inclusion dans 33500/33800/34990/35000.

Le revenu net 23600 des autres personnes est rapproché de leur déclaration
sur pièces et conserve sa source; il n'est pas un crédit calculé saisi.
Les revenus négatifs sont bornés à zéro pour le seuil. Revenus imposables,
revenus nets et calcul Québec du demandeur ne sont pas modifiés par ce crédit.
Les tests vérifient aussi l'ordre 42900/40500 et l'abattement Québec.

Le profil détaillé remplace la saisie fédérale médicale agrégée : le cumul
est refusé. Les anciens JSON chargent un profil vide, les nouveaux stockent
seulement les données brutes. Validation stricte des types, montants finis,
cents, dates, confirmations, clés JSON et identité du demandeur; refus des
profils explicites divergents de l'estimation à la sauvegarde. Validation au
rechargement et recalcul des résultats. Aucun dossier réel n'est transmis.

La GUI gère les personnes et reçus; modifications et changements de période
révoquent les confirmations. Résumé, trace et PDF montrent les bases, seuils,
références, parts et périodes. Les anciens profils médicaux restent disponibles.
Le rapprochement des rénovations multigénérationnelles tient compte des
nouveaux reçus, même lorsque le crédit médical après seuil est nul.

Limites logicielles de ce bloc : décès et périodes spéciales non couverts;
Québec familial traité en Priorité 6; ACT et supplément médical familiaux
encore à étendre. Les combinaisons avec leurs profils individuels sont
refusées quand le profil médical contient un conjoint ou une personne à
charge. Ces limites ne signifient pas une exclusion fiscale générale.

Validation ciblée : **228 passed, 5 warnings**. Suite complète :
**5247 passed, 8 warnings** (178,02 s). Rendu PDF familial vérifié visuellement.

### Bloc 5T — supplément médical familial, ligne 45200

Sources officielles 2025 :
- [ARC, ligne 45200](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-45200-refundable-medical-expense-supplement.html).
- [Feuille fédérale 2025, page 9](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf).

L'extension ajoute un mode familial explicite au profil 5D. La résidence
canadienne toute l'année, l'âge minimal de 18 ans et les autres conditions
restent vérifiés. Dans le périmètre salarié sans ajustements PUGE/REEI,
le revenu familial est le revenu net du demandeur plus celui du conjoint,
avec plancher zéro appliqué séparément. Le revenu d'une personne à charge
n'entre pas dans cette somme. Le minimum de travail de 4390 $ concerne
le demandeur, après les déductions 20700/21200/22900 couvertes.

Le revenu du conjoint est exclu en cas de rupture avec séparation d'au moins
90 jours incluant le 31 décembre 2025, ou de décès au plus tard à cette date.
Ces faits exigent une vérification comptable sur pièces; le profil conserve
le nom, la source et le revenu déclaré, même lorsque ce dernier est exclu.
Le choix « sans conjoint » peut couvrir une personne avec personnes à charge.

Calcul : max(min(1504, 25 % de 33200) - 5 % de max(revenu familial - 33294, 0), 0),
sous réserve du minimum de travail. La base 33200 vient du moteur familial
5S. Aucun montant de crédit calculé n'est saisi. Les lignes 33500/33800/34990/
35000, 42900/40500 et l'abattement restent ceux du calcul non remboursable;
45200 est ajouté une seule fois au rapprochement.

Les combinaisons 30300/32600 sont admises avec un conjoint et un revenu
concordants; 30400 reste incompatible avec un conjoint dans le profil annuel
actuellement couvert par ce bloc. Les identités sont aussi rapprochées des
reçus médicaux, des contributions politiques et des fonds de travailleurs.
Les mêmes contrôles s'appliquent à la sauvegarde sans estimation et au
rechargement. Ce sont des contrôles de cohérence des profils logiciels,
sans conclusion générale sur des situations conjugales plus complexes.

La GUI conserve les données familiales, révoque les confirmations après
modification et permet l'effacement. Une modification des reçus 5S révoque
aussi la validation du supplément. JSON rétrocompatible : anciens profils
individuels inchangés, nouveau revenu du conjoint sérialisé en chaîne décimale
au cent, clés inconnues et valeurs non finies refusées, résultat dérivé non
persisté, divergence avec l'estimation refusée. Trace et PDF distinguent le
revenu déclaré, le revenu retenu, la source et le résultat calculé.

Limites logicielles : l'ACT familiale est intégrée en 5U; son ancien profil
individuel ne peut être associé à ce mode familial. Le profil agrégé de frais
médicaux reste individuel et ne se cumule pas avec le mode familial; utiliser
5S. Travail autonome, 10400, assurance-salaire, 21500/23100, ajustements PUGE/
REEI, faillite et décès du demandeur restent hors de ce profil. Le revenu net
du conjoint provient de sa déclaration vérifiée et peut être négatif avant
le plancher; le demandeur reste dans les profils de revenus pris en charge.
Ces limites ne constituent pas des exclusions fiscales générales.

Validation ciblée : **227 passed, 5 warnings**. Suite complète :
**5308 passed, 8 warnings** (171,49 s). Rendu PDF familial vérifié visuellement.

### Bloc 5U — ACT familiale Québec, lignes fédérales 45300 et 41500

Sources officielles : [annexe 6 Québec 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s6/5005-s6-25e.pdf),
[admissibilité ARC 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-45300-canada-workers-benefit-cwb/who-is-eligible.html),
[attribution des RC210, ligne 41500](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-41500-canada-workers-benefit-cwb-advance-payments.html),
[LIR 122.7, admissibilité et attribution entre personnes](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.7.html)
et [LIR 122.71, paramètres provinciaux convenus](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.71.html).

Le nouveau sous-profil familial de 5E distingue le conjoint présent du
conjoint admissible à l'ACT. Résidence, études, détention et exemption
diplomatique sont consignées; les pièces et attributions sont vérifiées par
le comptable. Un enfant admissible est identifié avec sa naissance, le lien,
la cohabitation au 31 décembre et l'absence d'admissibilité propre à l'ACT.
Il doit avoir moins de 19 ans. Un enfant suffit à établir la catégorie;
son attribution doit respecter 122.7(10), sans désignation automatique par
le moteur ni double demande entre soutiens. La condition d'âge du demandeur
admet le parent ou conjoint de moins de 19 ans. L'exception aux études de
plus de treize semaines est couverte pour le demandeur ayant l'enfant admissible.

Le moteur suit les quatre colonnes de l'annexe 6 :

| Conjoint admissible | Enfant admissible | Seuil travail | Taux base | Maximum | Seuil réduction base | Seuil réduction supplément |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Non | Non | 2400 | 37,3 % | 3812,06 | 14170,05 | 33230,35 |
| Oui | Non | 3600 | 37,3 % | 5943,38 | 21787,19 | 51504,09 |
| Non | Oui | 2400 | 20 % | 2044,00 | 14341,56 | 24561,56 |
| Oui | Oui | 3600 | 23,9 % | 3808,23 | 22007,75 | 41048,90 |

Seuls les revenus du conjoint admissible sont ajoutés. Chaque revenu net
retenu est borné à zéro. L'exemption du second revenu prend le minimum de
16386 $, du travail et du net ajusté du **même membre**, celui dont le travail
est le plus faible; à égalité, colonne du conjoint. La réduction de base est
de 20 %. Le supplément utilise le travail personnel au-delà de 1200 $, avec
taux de 20 % si conjoint admissible, sinon 40 %, et maximum 851,31 $. Sa
réduction est de 10 % si le conjoint admissible est aussi admissible au CIPH,
sinon 20 %. Les deux composantes sont bornées séparément à zéro.

L'ACT de base n'est réclamée qu'une fois dans le couple. Ses avances regroupent
les cases 10 des deux conjoints chez le déclarant désigné, même si le conjoint
n'est pas admissible à l'ACT. Si personne ne réclame la base, le choix du
déclarant des avances est explicite. La case 11 demeure personnelle. 41500
est plafonnée à la propre 45300 du demandeur. Les avances augmentent 42000,
sans modifier 42900/40500 ni l'abattement. 45300 est ajoutée une seule fois
au rapprochement; aucun changement de revenu ou de crédit non remboursable.

Les garde-fous individuels sont levés seulement pour le sous-profil familial
validé. Les revenus et identités sont rapprochés de 30300, 32600, des reçus
politiques, des fonds et du médical 5S/5T. L'exemption ACT n'est jamais appliquée
au revenu familial de 45200. Les anciens profils individuels sont conservés.
Les profils du conjoint donneur à 32600 peuvent désormais contenir 45200 ou
l'ACT familiaux : son bénéficiaire, les revenus nets, le travail et le choix
du réclamant de la base sont contrôlés réciproquement lors du recalcul.

Le JSON stocke les données brutes du sous-profil, sans exemption ni prestation
calculée; ancien champ absent : famille vide. Decimal en chaînes au cent,
types stricts, clés inconnues refusées et divergence avec estimation refusée.
Contrôles de concordance à la sauvegarde et au rechargement. GUI avec
révocation des confirmations après modification, trace détaillant les étapes
de l'annexe 6 et PDF avec sources, revenus, exemption, composantes et avances.

Limites logicielles conservées : revenus de travail autres que 10100,
ajustements PUGE/REEI, choix de revenus exonérés, décès/faillite et situations
conjugales spéciales. Le conjoint étudiant est couvert comme non admissible
seulement si l'absence de personne à charge admissible pour lui est confirmée.
L'extension ci-dessous traite désormais le conjoint étudiant et l'attribution
distincte d'un enfant à chaque parent. La Priorité 5 n'est pas encore clôturée.

Validation ciblée et GUI : **299 passed, 5 warnings**. Suite complète :
**5416 passed, 8 warnings** (175,59 s). Rendu PDF familial vérifié visuellement.


### Correctif 5U — attribution unique et exception étudiante ACT

Arbitrage fiscal retenu pour le projet : pour l'application des paragraphes
122.7(2) et (3), l'attribution unique prévue à 122.7(10) conditionne également
l'exception étudiante de 122.7(1). Un étudiant à temps plein pendant plus de
13 semaines ne bénéficie pas de l'enfant attribué à l'autre parent pour
demeurer admissible. Il lui faut une autre personne à charge admissible
qui lui est attribuée exclusivement.

Références : [LIR 122.7(1), (5) et (10)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-122.7.html),
[admissibilité ARC 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-45300-canada-workers-benefit-cwb/who-is-eligible.html)
et annexe 6 Québec 2025 citée plus haut. Cette mise en œuvre applique
l'arbitrage fourni lors de la reprise; elle ne présente pas l'ancien refus
logiciel comme une exclusion fiscale générale.

Le profil distingue l'enfant attribué au demandeur de celui attribué au
conjoint (nom, naissance, admissibilité et attribution vérifiées). Un même
nom normalisé ne peut figurer des deux côtés, même avec des dates divergentes.
Les pièces et la confirmation d'attribution unique restent nécessaires pour
vérifier les identités et les attributions à d'autres soutiens. Un enfant
représentatif par parent suffit pour établir son exception et son barème;
le moteur ne choisit ni ne réattribue automatiquement l'enfant.

Le statut étudiant du demandeur est explicite; une confirmation contradictoire
d'absence d'études est refusée. Un demandeur étudiant sans enfant attribué
obtient zéro à 45300 et 41500, y compris pour le supplément CIPH.
Un conjoint étudiant sans enfant attribué est exclu des revenus familiaux,
mais ses avances RC210 suivent toujours les règles de l'étape 4.
Avec deux enfants distincts attribués, les deux étudiants peuvent conserver
leur exception, sous les autres conditions. Une seule demande de base dans
le couple est autorisée conformément à 122.7(5).

**Exemple arbitré** : A non étudiant, travail/net 12000 $; B étudiant,
travail/net 8000 $; enfant commun attribué à A, aucun autre enfant attribué
à B. B est non admissible; revenu retenu 12000 $, exemption second revenu 0.
Base = min(2044, (12000 - 2400) × 20 %) = **1920,00 $**.
Réduction = max(12000 - 14341,56, 0) × 20 % = 0.
Ligne 45300 = **1920,00 $**, hors supplément et sans avances dans cet exemple.
L'hypothèse 3808,23 $ est écartée pour ces mêmes données.
Si B possède un autre enfant admissible distinct qui lui est attribué,
son revenu est inclus : travail familial 20000 $, net ajusté après exemption
8000 $ = 12000 $, base min(3808,23, 16400 × 23,9 %) = 3808,23 $.

JSON ancien sans nouveaux champs : valeurs vides/fausses, comportement
historique conservé. Contrôles stricts à la lecture; les dossiers conjoints
chargés via 32600 doivent porter des attributions et statuts étudiants
réciproquement cohérents. Aucun changement de formule du transfert 32600.
GUI : saisie distincte et révocation des confirmations après modification.
Trace/PDF : attribution à chaque parent et admissibilité après exception.

Validation ciblée, GUI et intégration : **268 passed, 5 warnings**.
Suite complète : **5436 passed, 8 warnings** (180,62 s), avec `--capture=sys`.
PDF de l'attribution étudiante vérifié visuellement; aucun artefact de test livré.


### Bloc 5V — combinaison 30400 / 30500, même enfant mineur avec infirmité

Sources 2025 : [ARC, ligne 30500](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30499-30500-canada-caregiver-infirm-children-under-18-years.html),
[RC4064](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4064/disability-related-information.html),
[ARC, ajustements courants des lignes 30400/30500](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/review-your-tax-return-cra/common-adjustments.html).

Règle officielle : pour son enfant mineur avec infirmité, le parent réclamant
30400 peut réclamer le montant aidant de 2687 $ à 30500, sous les conditions
de lien, dépendance, aide accrue et preuve médicale. Ces 2687 $ ne sont pas
ajoutés une seconde fois à la base de 30400.

Périmètre 5V : un même enfant biologique/adopté, un parent sans conjoint toute
l'année, sans garde partagée ni pension alimentaire; conditions historiques
de résidence et de soutien maintenues. Le nouveau mode est explicite dans
les deux profils; leur référence locale d'enfant (sans NAS) doit concorder.
Le comptable confirme l'identité réelle, les pièces et l'unicité du réclamant.
Le moteur ne détermine pas automatiquement une admissibilité médicale.

30400 = max(montant personnel applicable au parent - revenu net enfant, 0).
30500 = 2687 $. Exemple au revenu du parent de 51515 $ et de l'enfant de
4000 $ : 30400 = 12129 $, 30500 = 2687 $. Un revenu enfant élevé peut ramener
30400 à zéro sans réduire le montant fixe 30500 dans ce profil admissible.
Les deux bases alimentent 33500/33800 puis 34990/35000 selon l'ordre T1;
42900/40500 et l'abattement suivent le calcul existant, sans crédit ajouté
deux fois. Aucun changement de revenu ni de calcul Québec.

L'ancien profil 30500 avec deux parents demeure inchangé et ne se combine
pas implicitement avec 30400. Les situations d'autres enfants, de garde
partagée, de pensions et d'attribution à un autre réclamant restent à étendre;
ces limites logicielles ne constituent pas des interdictions fiscales.

Persistance : anciens champs absents = mode désactivé; nouvelles données
brutes conservées, types/clés contrôlés, références vérifiées à la sauvegarde
et au rechargement. Le profil combiné est inféré de l'estimation si omis
lors de la sauvegarde; toute divergence explicite est refusée.
GUI : référence commune, preuve médicale, confirmations révoquées après
modification. Trace/PDF identifient la combinaison et n'affirment plus
l'absence d'infirmité ou une résidence avec deux parents pour ce mode.

Validation ciblée, GUI et intégration : **128 passed, 5 warnings**.
Suite complète : **5465 passed, 8 warnings** (172,18 s), avec `--capture=sys`.
Le PDF combiné a été vérifié visuellement.


### Bloc 5W — partage du montant aidant 30450 entre soutiens

Sources : [Annexe 5 fédérale 2025, page 5](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s5/5000-s5-25e.pdf),
[ARC, ligne 30450](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30450-caregiver-infirm-dependant.html),
[LIR 118(4)d) et 118(6)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.html).

Règle officielle : plusieurs soutiens peuvent partager le montant pour une
même personne, sans dépasser ensemble le maximum permis après réduction
selon son revenu. L'entente fixe les parts; le moteur ne choisit pas la
répartition et ne détermine pas l'admissibilité médicale.

Périmètre logiciel : une seule personne adulte, admissibilité du profil
30450 existant confirmée, sans pension alimentaire ni réclamation 30300/30400
pour la même personne. Enfants/petits-enfants : exception de résidence de
118(6)a); les autres liens nécessitent la résidence au Canada dans l'année.
Les fiches de plusieurs personnes à charge ont ensuite été intégrées par 5X.

Calcul : plafond = min(8601, max(28798 - revenu 23600, 0)).
Part du dossier = plafond - somme attribuée aux autres soutiens.
Cette somme est un fait de l'entente documentée, pas une saisie manuelle du
crédit calculé. Le profil refuse une somme négative, supérieure au plafond,
non finie ou contenant une fraction de cent. Exemple : revenu 25000 $,
plafond 3798 $, parts des autres soutiens 1500 $ : 30450 = 2298 $.
Si le plafond est entièrement attribué ailleurs, la part et le nombre 51120
du dossier sont zéro. Le crédit de 14,5 % est intégré aux bases 33500/33800,
34990/35000 puis 42900/40500; aucun changement de revenu ni du calcul Québec.

Le comptable confirme l'entente entre tous les soutiens, l'identité locale de
la personne et la somme des parts attribuées ailleurs. Référence sans NAS et
source de l'entente obligatoires. Aucun rapprochement automatique avec des
dossiers externes non liés; un partage non convenu reste refusé. La preuve
médicale, les autres exclusions et la validation comptable restent exigées.

JSON rétrocompatible : champs absents = aucun partage, somme zéro. Données
brutes conservées en Decimal texte, types et clés contrôlés; profil partagé
inféré de l'estimation si omis, divergence explicite refusée. GUI : référence,
source et somme convenue ailleurs; modification révoquant les confirmations.
Trace/PDF : plafond réduit, parts ailleurs et solde du dossier visibles.
Le PDF synthétique a été contrôlé visuellement sans artefact livré.

Validation ciblée moteur, intégration et GUI : **78 passed, 5 warnings**.
Suite complète : **5501 passed, 8 warnings** (173,15 s), avec `--capture=sys`.


### Bloc 5X — plusieurs personnes à charge, ligne 30450 / nombre 51120

Sources 2025 : [Annexe 5, pages 1 et 5](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s5/5000-s5-25e.pdf),
[ARC, ligne 30450](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30450-caregiver-infirm-dependant.html).
L'annexe demande de calculer le montant séparément pour chaque personne,
puis de porter la somme à 30450 et le nombre de personnes réclamées à 51120.

L'extension lève la limite d'une seule personne du profil 30450. Chaque fiche
conserve ses propres faits, preuves et exclusions : lien admissible, âge 18+
dans l'année, dépendance en raison de l'infirmité, résidence lorsque requise,
absence de 30300/30400 pour cette personne et absence de pension alimentaire.
Le partage 5W s'applique séparément à chaque fiche. Les mêmes critères ne sont
pas déduits automatiquement du diagnostic ou du nom : confirmation comptable
obligatoire par fiche, puis confirmation des identités distinctes de l'ensemble.

Pour chaque personne : min(8601, max(28798 - revenu 23600, 0)) moins les
parts convenues ailleurs. Le total 30450 additionne les parts du dossier;
51120 compte celles qui sont positives. Le crédit de 14,5 % est arrondi une
seule fois après la somme. Deux bases de 1,01 $ donnent ainsi 0,29 $ de crédit.
Exemple : parent A, revenu zéro, sans partage = 8601 $; parent B, revenu
25000 $, parts ailleurs 1500 $ = 2298 $; total 10899 $, 51120 = 2.
Intégration aux bases 33500/33800, 34990/35000 puis 42900/40500 inchangée;
les revenus et le calcul Québec ne sont pas modifiés.

Référence locale sans NAS, nom et naissance ISO obligatoires. Références en
double et même nom normalisé avec même naissance refusés. L'identité réelle
et l'absence de doubles demandes dans des dossiers externes restent vérifiées
par le comptable. Pas de listes imbriquées ni de faits individuels concurrents
au niveau de l'ensemble. Le profil historique reste disponible et compatible.

JSON : liste des fiches brutes, Decimal texte, clés/types contrôlés à la lecture,
ancien champ absent = liste vide. Profil inféré depuis l'estimation si omis;
divergence explicite refusée. GUI : ajout, modification, retrait, réouverture;
modification des faits révoquant les confirmations individuelles et modification
de la liste révoquant les confirmations globales. La conversion d'un profil
historique reprend ses faits enregistrés et exige de compléter son identité.
Trace/PDF détaillent le calcul, les sources et les validations de chaque personne,
puis le total; le PDF synthétique a été vérifié visuellement.

Validation ciblée moteur, stockage, trace/PDF et GUI : **133 passed, 5 warnings**.
Les fiches de la liste restent strictes même si leurs nouveaux champs sont absents.

Suite complète finale : **5537 passed, 8 warnings** (175,46 s), avec `--capture=sys`.


### Bloc 5Y — plusieurs enfants, lignes 30499 / 30500

Sources 2025 : [ARC, ligne 30500](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30499-30500-canada-caregiver-infirm-children-under-18-years.html),
[Annexe 5 fédérale, pages 1 et 6](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-s5/5000-s5-25e.pdf).
Règle officielle : 2687 $ par enfant admissible de moins de 18 ans à la fin
de l'année, une seule réclamation par enfant. Le montant entier est permis
l'année de naissance ou d'adoption; il n'est pas réduit au prorata des mois.

Périmètre de la liste 5Y : enfants biologiques/adoptés du demandeur ou de son
conjoint, vivant avec leurs deux parents toute l'année (pendant leur vie en
2025 pour un nouveau-né), sans garde partagée, pension alimentaire ni transfert
32600 de leur montant. Chaque fiche confirme l'infirmité, la dépendance durable,
l'aide accrue, la preuve médicale/T2201 et l'absence d'autre réclamant.
Ces confirmations comptables ne sont pas une détermination médicale automatique.
La combinaison 30400/30500 de 5V reste dans son parcours individuel; elle n'est
pas convertie silencieusement en liste. Les autres attributions familiales de
30500 restent à étendre : cette limite logicielle n'est pas une règle fiscale.

30499 = nombre d'enfants validés; 30500 = nombre × 2687 $.
Crédit = 14,5 % du montant total, arrondi une seule fois : deux enfants donnent
5374 $ de base et 779,23 $ de crédit, pas deux crédits individuels arrondis.
Les bases 33500/33800 et 34990/35000 suivent l'ordre T1 existant, puis 42900/40500;
aucun changement du revenu ni du calcul Québec.

Référence locale sans NAS, nom et naissance ISO par enfant, âge recalculé pour
contrôle, références ou identités (nom normalisé et naissance) en double refusées.
Les identités réelles et les demandes externes sont rapprochées par le comptable.
Aucune liste imbriquée ni faits concurrents au niveau de l'ensemble.

JSON : données brutes par fiche, anciens champs absents = liste vide. Types et
clés stricts dans les nouvelles fiches même au format historique, inférence depuis
l'estimation si omise et divergence explicite refusée. Les combinaisons 30400 hors
de ce mode sont aussi refusées à la sauvegarde et au rechargement sans estimation.
GUI : ajout/modification/retrait, conservation des faits lors d'une conversion
historique, identités à compléter, révocation des confirmations individuelles
et globales après modification. Trace/PDF : enfants, sources et preuves distincts,
puis nombre, base totale et crédit; pas de saisie manuelle du montant calculable.

Validation ciblée moteur, stockage, trace/PDF et GUI : **119 passed, 5 warnings**.
Le PDF synthétique de deux enfants a été contrôlé visuellement.
Suite complète : **5574 passed, 8 warnings** (178,87 s), avec `--capture=sys`.


### Bloc 5Z — partage du montant pour achat d'habitation, ligne 31270

Sources : [ARC, ligne 31270, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-31270-home-buyers-amount.html),
[LIR 118.05(1) à (4)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/page-90.html).
Plusieurs personnes admissibles à l'égard de la même habitation peuvent répartir
le montant, sans dépasser ensemble 10000 $. Cela comprend des conjoints admissibles
ou d'autres personnes admissibles ayant acquis ensemble l'habitation. Si un seul
conjoint est admissible, lui seul peut réclamer : le partage exige leur admissibilité.

Périmètre : première habitation, critères historiques d'acquisition, propriété,
occupation et pièces conservés; exception liée au handicap toujours exclue de
ce profil logiciel. Le comptable confirme l'admissibilité de tous les participants
au partage et leur entente. Une référence d'habitation et la source de l'entente
entre tous les acquéreurs sont obligatoires; aucun rapprochement automatique de
dossiers externes non liés. Le moteur ne détermine pas l'admissibilité juridique
à partir de l'adresse seule et ne choisit pas la répartition optimale.

Nouveau mode partagé : 31270 = 10000 $ moins la somme des parts attribuées aux
autres acquéreurs dans l'entente. Exemple : 4000 $ ailleurs donne 6000 $ dans le
dossier, soit 870 $ de crédit à 14,5 %. Les sommes négatives, au-delà de 10000 $,
non finies ou avec fractions de cent sont refusées. Une part entièrement attribuée
ailleurs donne zéro dans le dossier. Le champ historique `montant_reclame` doit
rester zéro dans ce mode, pour éviter deux sources de montant. Le total alimente
33500/33800, puis 34990/35000 et 42900/40500 dans l'ordre existant. Revenu et Québec
inchangés. L'ancien profil sans partage conserve son montant explicite à la lecture.

JSON : nouvelles données brutes, Decimal texte, types et clés stricts; ancien
champ absent = partage désactivé. Profil partagé inféré depuis l'estimation si
omis; divergence explicite refusée. GUI : choix du partage, montant dérivé en
lecture seule, faits de l'entente et confirmations révoquées après modification.
Trace/PDF : plafond commun, parts ailleurs, solde et sources. L'ancien test PDF
exigeant un refus général du partage a été actualisé pour vérifier la limite
encore présente, l'exception handicap, sans affaiblir les tests de plafond.

Validation ciblée moteur, stockage, trace/PDF et GUI : **96 passed, 5 warnings**.
PDF synthétique du partage vérifié visuellement; aucun artefact de test livré.
Suite complète : **5610 passed, 8 warnings** (175,47 s), avec `--capture=sys`.

### Bloc 5AA — partage des dépenses d'accessibilité, ligne 31285

Sources : [ARC, ligne 31285, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-31285-home-accessibility-expenses.html),
[feuille fédérale 2025, page 4](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5000-d1/5000-d1-25e.pdf),
[LIR 118.041, version couvrant 2025](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-118.041-20220623.html).
La feuille plafonne d'abord les dépenses admissibles à 20000 $, puis retranche
les demandes des autres particuliers déterminés et admissibles du même logement.
Le plafond est commun, même si plusieurs particuliers déterminés y habitent.
Le plafond annuel par particulier déterminé demeure applicable à plusieurs logements.

Périmètre logiciel du nouveau mode : demande pour soi-même, contribuable de
65 ans ou plus ou admissible au CIPH, propriétaire et occupant du logement au
Canada. Tous les participants habitent le même logement; il s'agit du seul
logement admissible en 2025 pour tous les particuliers déterminés concernés.
Cette restriction aux logements uniques évite de prétendre gérer les plafonds
croisés en cas de déménagement. Demandes pour autrui, autres logements et
ventilation entreprise/location restent hors de ce mode, sans être déclarés
fiscalement inadmissibles. L'admissibilité des participants, leurs montants et
l'entente de tous sont confirmés avec une référence du logement et une source.
Le comptable rapproche les dossiers externes : aucun rapprochement automatique
ni optimisation du partage. Les justificatifs des travaux restent obligatoires.

Formule : `31285 = min(dépenses communes admissibles, 20000) − demandes ailleurs`.
Exemple : 25000 $ de dépenses, 4000 $ ailleurs donnent 16000 $ dans le dossier
et 2320 $ de crédit à 14,5 %. Une attribution intégrale ailleurs donne zéro;
une somme supérieure aux dépenses plafonnées est refusée. Les dépenses brutes
peuvent dépasser 20000 $ dans ce mode; limite technique 999999999,99 $, montants
Decimal finis, non négatifs et au cent près. Le profil historique sans partage
conserve son contrat. Les lignes 33500/33800, 34990/35000 puis 42900/40500 utilisent
le solde calculé; revenus et Québec inchangés. Le cumul avec les frais médicaux
reste permis pour une dépense admissible aux deux crédits en **2025**, selon
118.041(4) alors applicable; aucune transposition de sa suppression en 2026.

JSON : données brutes du partage, champs absents compatibles, types et clés
stricts pour le nouveau profil; inférence depuis l'estimation et divergence
explicite refusée. GUI : solde en lecture seule, révocation de l'entente, des
confirmations du partage et de la validation comptable après modification.
Trace et PDF : dépenses brutes, plafond, demandes ailleurs, solde et sources.

Validation ciblée moteur, ancien profil, stockage, GUI, trace et PDF :
**109 passed, 5 warnings**. PDF synthétique vérifié visuellement.
Suite complète : **5655 passed, 8 warnings** (195,84 s), avec `--capture=sys`.

### Bloc 5AB — enfants distincts à 30500 et transfert du conjoint à 32600

Sources : [ARC, ligne 30500, année 2025](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/line-30499-30500-canada-caregiver-infirm-children-under-18-years.html),
[annexe 2 Québec 2025](https://www.canada.ca/content/dam/cra-arc/formspubs/pbg/5005-s2/5005-s2-25e.pdf).
Un enfant ne peut être réclamé qu'une fois à 30500; un montant inutilisé peut
être transféré au conjoint selon l'annexe 2. Le refus historique de deux
demandes 30500 a été reproduit avec deux enfants distincts, puis remplacé par
un contrôle des fiches nominatives 5Y dans les deux dossiers.

Périmètre : enfants biologiques/adoptés, infirmité et preuve validées, vivant
avec leurs deux parents toute l'année, sans garde partagée ni pension. Les
conditions 5K du couple et de l'autorisation demeurent obligatoires. Lorsque
les deux dossiers réclament 30500, ils doivent utiliser les fiches identifiées;
une référence commune ou une identité commune (nom normalisé et naissance)
bloquent le calcul, même si le solde transférable est nul. Le comptable confirme
les identités réelles, l'attribution unique et les dossiers externes. Les profils
historiques sans identité restent utilisables lorsqu'un seul conjoint réclame
30500, selon leur contrat antérieur; ils ne permettent pas deux demandes.

Les confirmations historiques d'absence de transfert décrivent le dossier
personnel **avant** l'autorisation séparée 5K, comme prévu depuis ce bloc.
Chaque enfant propre donne 2687 $ à 30500; les enfants du conjoint alimentent
la ligne 2 de son annexe 2, puis son solde inutilisé à 32600. Aucun enfant du
conjoint n'est ajouté une seconde fois à la ligne 30500 du bénéficiaire.
Pour un seul enfant chez le conjoint, avec uniquement des intérêts et le
montant personnel de 16129 $ : revenu de 10000 $ → transfert de 2687 $;
17000 $ → réduction de 871 $ et transfert de 1816 $; 18816 $ → transfert nul.
Les autres montants de l'annexe 2 restent traités par sa formule complète.

JSON : les fiches brutes dans l'instantané existant sont conservées; aucun
nouveau résultat dérivé persisté. Vérification de l'attribution aussi à la
sauvegarde et au rechargement sans estimation. GUI : listes 5Y et import 5K
réutilisés, refus du doublon dès l'aperçu/application, noms et dates du conjoint
dans l'aperçu, la trace et le PDF. Les modifications de source révoquent toujours
les confirmations; une correction chez le conjoint impose sa réimportation.
Revenus et Québec inchangés; 33500/33800/34990/35000 et 42900/40500 recalculés.

Validation ciblée, dont attributions inversées, transferts maximal/partiel/nul,
plusieurs enfants, doublons, anciens profils, JSON injecté, GUI et PDF :
**123 passed, 5 warnings**. PDF synthétique vérifié visuellement.
Suite complète : **5674 passed, 8 warnings** (180,21 s), avec `--capture=sys`.

### Audit de fin du périmètre courant de la Priorité 5

L'inventaire d'ouverture et les audits intermédiaires ci-dessus décrivent
l'historique. Les familles prévues à la Priorité 5 ont désormais un parcours
calculé, persisté et vérifié pour les profils bornés décrits dans chaque bloc :

| Famille | Livraison |
| --- | --- |
| Calcul fédéral complet des crédits, 34990 et hauts revenus | 5A, 5J |
| Prêts étudiants, formation, scolarité et reports/transferts | 5B, 5C, 5F à 5H, 5K |
| Dons monétaires et reports | 5I, 5J |
| ACT et supplément médical, individuels et familiaux | 5D, 5E, 5T, 5U et arbitrage étudiant |
| Autres crédits documentés : bénévoles, adoption, contributions politiques, fonds, éducateur, rénovation multigénérationnelle | 5L à 5Q |
| Handicap et transferts; frais médicaux familiaux | 5R, 5S |
| Combinaisons, personnes à charge multiples et partage des crédits personnels | 5V à 5AB |

Les anciens blocages de première tranche ont été retirés de l'orchestrateur
par 5A; les anciennes fonctions de compatibilité ne pilotent plus ce refus.
Les refus globaux du partage 30450, 31270, 31285 et des deux demandes 30500
ont été remplacés dans les nouveaux parcours par les contrôles documentés.
Recherche des mentions TODO, non pris en charge, garde-fou, provisoire,
hors périmètre et à intégrer effectuée : les mentions historiques ne prouvent
pas une absence actuelle de fonctionnalité; l'entrée 5W devenue obsolète est
corrigée pour renvoyer à 5X.

Cette clôture des familles courantes ne signifie pas une T1 universelle.
Les contextes avancés encore refusés comprennent notamment garde partagée,
pensions alimentaires et changements d'union dans les crédits familiaux,
transferts 32600 réciproques, certains profils de dons non monétaires,
plusieurs logements pour le partage 31285, résidence partielle, décès/faillite
et combinaisons de revenus hors des parcours existants. Ils restent des limites
logicielles explicites à reprendre dans l'audit des profils avancés (Priorité 7),
sans être présentés comme des interdictions fiscales. Aucune garde nécessaire
n'a été retirée pour déclarer la suite verte.

La suite complète 5AB ci-dessus valide cet état. La Priorité 6 prend la suite :
annexe B combinée, puis autres familles de crédits Québec prévues à la roadmap,
avec leurs propres sources Revenu Québec. Le produit n'est pas encore déclaré
prêt pour la version 1.0 : Priorités 6 et 7 et audit global restent à réaliser.


### Bloc 6A livré — annexe B combinée sans conjoint, ligne 361

Les montants pour personne vivant seule et pour âge/retraite peuvent désormais
être combinés dans un calcul commun. Selon l’[annexe B officielle 2025, parties A/B](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.B%282025-12%29.pdf),
on additionne les composantes des lignes 20 à 28 avant de soustraire **une seule**
réduction de 18,75 % de l’excédent du revenu familial sur 42 090 $.
Le résultat, au minimum zéro, constitue la ligne 361; le crédit non remboursable
est de 14 %. Dans ce périmètre sans conjoint, le revenu familial est le revenu
net Québec recalculé du contribuable, et aucune part n’est attribuée à un conjoint.

Composantes conservées : personne seule 2 128 $, âge 3 906 $ si naissance avant
1961, retraite admissible nette × 1,25 plafonnée à 3 470 $. L’additionnel
monoparental conserve les conditions du [guide RQ, ligne 361](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/350-a-398-1-credits-dimpot-non-remboursables/ligne-361/) :
2 627 $ moins 218,92 $ par mois donnant droit à l’Allocation famille, enfant
majeur aux études admissible et aucun droit à cette allocation en décembre.
Le libellé GUI précise le droit mensuel, plutôt que la date de paiement.

Exemple synthétique vérifié : revenu net Québec 50 000 $, personne seule,
âge admissible et pension admissible de 50 000 $. Total ligne 30 =
2 128 + 3 906 + 3 470 = 9 504 $; réduction ligne 31 = 1 483,13 $;
ligne 361 = **8 020,87 $**; crédit = **1 122,92 $**. Les revenus et l’impôt
fédéral restent inchangés; l’impôt Québec et le rapprochement appliquent ce
crédit une seule fois, avec plancher d’impôt à zéro.

Périmètre logiciel : les deux profils doivent confirmer la combinaison et
présenter le même revenu net. Les anciennes confirmations d’absence de l’autre
montant doivent être désactivées. Sans ces confirmations communes, l’ancienne
protection contre une combinaison non validée reste active. Les fonctions de
calcul isolées refusent le mode combiné, afin d’empêcher deux réductions.
Résidence Québec/Canada toute l’année, absence de conjoint, habitation,
conditions d’âge et nature des revenus restent soumis aux validations existantes.
La résidence partielle, les décès, les transferts entre conjoints et les règles
particulières hors profils existants ne sont pas étendus par 6A. Ce sont des
limites de prise en charge, et non une déclaration d’inadmissibilité fiscale.

Le JSON ajoute une confirmation brute dans chacun des deux profils : ancienne
absence du champ = mode historique. Les résultats sont recalculés, non saisis.
Les types et clés du nouveau format, la cohérence entre profils et la divergence
avec l’estimation sont contrôlés. La GUI conserve les données justificatives,
révoque la combinaison et la validation comptable après changement, et exige
une confirmation dans chaque dialogue. Trace, résumé et PDF présentent une
section commune avec les composantes, réduction, crédit et sources, sans
additionner les anciens crédits séparés.

Validation ciblée 6A et régressions : **251 passed, 5 warnings**. Tests couvrant
seuils, revenus nuls/positifs, extinction, composantes facultatives, supplément
mensuel, confirmations contradictoires, types, JSON ancien/nouveau, feuillets
pensions, rapprochement, GUI, trace et PDF. Les avertissements ciblés proviennent
de la dépendance SWIG. La suite complète et la publication sont consignées au
journal de mission après exécution.

Journal 6A : suite complète avant commit **5710 passed, 8 warnings**
(`--capture=sys`, 190,79 s). Les deux anciennes assertions de libellés GUI ont
été actualisées pour la combinaison désormais autorisée et le droit mensuel à
l’allocation; le test GUI exécuté confirme le comportement. Aucun test supprimé
ni désactivé. Les 8 warnings restent ceux de SWIG et de la copie de police
openpyxl déjà présents. Fichiers : moteur commun, profils âge/retraite et
personne seule, estimation, stockage, GUI, trace, PDF, documentation et tests.


### Bloc 6B livré — intérêts étudiants Québec, ligne 385 et annexe M

Sources propres au Québec : [RQ, ligne 385](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/350-a-398-1-credits-dimpot-non-remboursables/ligne-385/),
[annexe M 2025](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D.M%282025-12%29.pdf)
et [TP-1 2025, page 4](https://www.revenuquebec.ca/documents/fr/formulaires/tp/2025-12/TP-1.D%282025-12%29.pdf).
La limite historique indiquée dans 5B concernait son périmètre fédéral; 6B ajoute
un profil Québec indépendant. Aucun solde ni choix fédéral n’est copié implicitement.

**Règle officielle.** Le contribuable doit être l’emprunteur du prêt admissible;
les paiements peuvent provenir de lui ou d’une personne liée. Les lois visées
sont celles de l’aide financière aux études, des prêts étudiants fédéraux,
de l’aide financière fédérale aux étudiants, des prêts aux apprentis, ou d’une
autre province pour les études postsecondaires. Prêts privés, prêts intégrés
à un autre type de prêt et intérêts issus d’un jugement sont exclus.
Les intérêts admissibles inutilisés depuis 1998 sont reportables aux années
suivantes, sans la fenêtre de cinq ans du fédéral.

**Calcul.** Annexe M : ligne 46 (solde inutilisé antérieur) + ligne 48 (paiements
2025) = ligne 52 (disponible). Le contribuable choisit une partie ou la totalité
à la ligne 385, reprise à la ligne 60. Le report ligne 62 est le disponible
moins cette réclamation. Ce choix fiscal est une entrée; le crédit n’est jamais
saisi. Exemple synthétique : solde 2 000 $, paiements 1 000 $, réclamation
1 200 $ → disponible 3 000 $, crédit 240 $, report 1 800 $.

**Intégration TP-1.** Le taux est **20 %**, aux lignes 388/389. Le moteur arrondit
la somme des bases 381 et 385 une seule fois et soustrait le crédit médical déjà
comptabilisé pour déterminer l’ajout au crédit. Test du cent : 0,02 $ de base
381 + 0,02 $ de base 385 → 0,01 $ à 389, contrairement à deux arrondis séparés.
L’impôt Québec est réduit avec plancher zéro avant les crédits pour dividendes
et impôt étranger. Les revenus et les résultats fédéraux restent inchangés.
Les intérêts réclamés ne retournent pas au report si le crédit ne réduit pas
l’impôt; l’interface explique ce choix, sans optimisation automatique.

**Périmètre et validation comptable.** Pièces de paiement, loi du prêt, lien du
payeur et solde Québec doivent être confirmés. La ligne 46 provient de l’annexe M
2024, de l’avis correspondant ou d’une reconstitution documentée des intérêts
1998–2024 jamais utilisés. Le profil 6B est borné aux résidents Québec/Canada
toute l’année, vivants, sans faillite ni transfert de crédit. Ces dernières
bornes sont des limites logicielles; elles ne remplacent pas les règles des cas
spéciaux. Les frais médicaux demeurent soumis à leur périmètre existant.

**Chaîne complète.** Profil immuable et Decimal au cent; types et clés JSON
stricts; absence de profil dans un ancien JSON = profil vide. Sauvegarde des
entrées, inférence depuis l’estimation, refus des divergences et recalcul.
Dialogue dédié avec crédit/report en lecture seule, révocation des confirmations
après changement, réouverture et effacement. Résumé, trace et PDF indiquent les
lignes 46/48/52/60/62, 385/388/389, source, validation et caractère non remboursable.
Aucune récupération automatique d’avis ni transmission à Revenu Québec.

Validation ciblée 6B + régressions 5B/médical : **187 passed, 5 warnings**.
Couverture : réclamation nulle/partielle/totale, reports anciens, payeur lié,
montants/types invalides, plafonnement au disponible, arrondi commun, impôt nul,
indépendance fédérale, JSON ancien/nouveau/divergent, GUI, trace et PDF.
Journal précédent 6A : commit `a619366`, 13 fichiers, suites avant/après commit
**5710 passed, 8 warnings**, push réussi et dépôt propre avant ouverture de 6B.

Journal 6B : suite complète avant commit **5781 passed, 8 warnings**
(`--capture=sys`, 193,19 s), diff sans erreur, PDF synthétique vérifié visuellement.


### Bloc 6C livré — achat d’une première habitation Québec, ligne 396

Références : [RQ, ligne 396 pour 2025](https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/comment-remplir-votre-declaration-de-revenus/aide-par-ligne/350-a-398-1-credits-dimpot-non-remboursables/ligne-396/)
et [TP-752.HA, version 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/tp/TP-752.HA%282025-10%29.pdf).
Le plafond de 1 400 $ est un crédit partagé par habitation. Le formulaire
limite aussi la demande à son propre plafond fiscal :
`max(401 - arrondi((359 + 361 + 367) × 14 %) - 391 - 397, 0)`.
La ligne 396 est le minimum de ce plafond et de `1400 - autres demandes 396`.
Elle ne doit pas être fixée automatiquement à 1 400 $.

Les sources exigent une habitation admissible au Québec, acquise par le
contribuable ou son conjoint, avec droit publié et habitation habitable.
Pour la première habitation, ni le contribuable ni son conjoint ne doivent
avoir possédé une habitation qu’il occupait depuis le 1er janvier 2021 jusqu’à
l’acquisition. L’intention d’en faire la résidence principale dans l’année
suivant l’acquisition est confirmée. Les parts des autres demandeurs admissibles
sont documentées; chaque demandeur doit établir son propre formulaire.

Périmètre logiciel 6C : première habitation acquise en 2025, contribuable vivant,
résident Québec/Canada toute l’année, sans faillite ni transfert de crédit.
L’exception handicap et les autres cas spéciaux restent à traiter séparément;
ces exclusions logicielles ne signifient pas une inadmissibilité fiscale.
La référence de l’habitation, date réelle, acte, critères et entente de partage
font l’objet de validations comptables. Aucune admissibilité détaillée automatique.

Le moteur reçoit les composantes fiscales recalculées : 359 inclut le
redressement 358, 361 inclut l’annexe B commune, et 397 le crédit de cotisations.
Le paramètre 367 est prévu dans la fonction pure mais reste nul dans
l’orchestrateur jusqu’à livraison de ce bloc. Depuis 6D, la ligne 391 recalculée
alimente aussi ce plafond. Le crédit final est appliqué une fois, avant les
crédits dividendes/étranger, avec plancher d’impôt zéro. Handicap, médical,
scolarité et dons ne sont pas soustraits pour déterminer le plafond spécifique
de TP-752.HA, même s’ils réduisent l’impôt final. Le fédéral et les revenus
restent inchangés; son profil 31270 est distinct.

Exemples synthétiques vérifiés : impôt 401 de 5 000 $, base 359 de 18 571 $,
autres parts de 400 $ → plafond fiscal 2 400,06 $, part disponible 1 000 $,
ligne 396 de 1 000 $. Avec impôt 401 de 3 000 $ et aucun partage, la ligne 396
est limitée à 400,06 $. L’impôt final peut déjà être nul à cause du médical :
le crédit calculé demeure traçable, mais ne crée aucun remboursement supplémentaire.

JSON rétrocompatible : ancien dossier sans profil = profil vide; seuls les
faits et parts convenues sont persistés. Types, cents, date et clés contrôlés;
refus des profils divergents de l’estimation. GUI dédiée, réouverture, effacement,
révocation des confirmations après modification; aucun crédit propre saisi.
Résumé, trace et PDF affichent les deux plafonds, leur minimum, les sources,
la validation et les limites. Tests ciblés avec régressions 5Z/6A/6B :
**202 passed, 5 warnings**; couvrent seuils, partage, impôt nul, 358/361/397,
combinaison médicale, indépendance fédérale, JSON, GUI, trace et PDF.

Journal précédent 6B : commit `5bdb095`, 11 fichiers; suites complètes avant et
après commit **5781 passed, 8 warnings**; push réussi, dépôt propre avant 6C.

Journal 6C : suite complète avant commit **5843 passed, 8 warnings**
(`--capture=sys`, 184,28 s), diff sans erreur et PDF synthétique vérifié visuellement.


### Bloc 6D livré — prolongation de carrière Québec, ligne 391

Sources 2025 : [RQ, prolongation de carrière](https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-prolongation-de-carriere/)
et [TP-752.PC, version 2025-10](https://www.revenuquebec.ca/documents/fr/formulaires/tp/TP-752.PC%282025-10%29.pdf).
Le seuil d’âge est **65 ans au 31 décembre 2025**. Les paramètres 2024 pour les
60–64 ans ne s’appliquent pas. Le maximum est de 1 750 $, avec extinction à
81 500 $ de revenu net. Ce crédit est non remboursable.

Formule 2025 : base = `min(max(revenu de travail admissible - 7500, 0), 12500)`;
crédit brut = base × 14 %; réduction = `max(revenu net 275 - 56500, 0) × 7 %`.
Le crédit réduit, au minimum zéro, est ensuite plafonné à
`max(401 - (359 + 361 + 367) × 14 %, 0)` selon les lignes 47 à 50 du formulaire.
Chaque multiplication monétaire est arrondie au cent. Le plafond utilise la
base commune 359/361/367, et non le solde après tous les autres crédits.

Périmètre salarié 6D : revenus de travail limités au salaire Québec du dossier,
sans lien de dépendance avec l’employeur ou un membre d’une société de personnes
employeuse, sans rétroactivité relative à une année passée, sans revenu d’ancien
emploi case 211 ni déduction 293/297 applicable au salaire. Ces confirmations
justifient des lignes 11 et 13 nulles. La présence d’une case 211 non nulle bloque
explicitement ce profil. Les revenus admissibles d’entreprise, de recherche,
de protection des salariés ou d’autres programmes restent à intégrer avec leurs
blocs avancés : ils ne sont pas déclarés fiscalement inadmissibles.

Le profil exige naissance, source et confirmations comptables, résidence
Québec/Canada toute l’année, contribuable vivant et sans faillite. La naissance
est rapprochée de l’âge du profil pensions lorsqu’il est actif. Salaire, revenu
net, impôt brut et annexe B proviennent de l’estimation; aucun crédit ni revenu
calculable n’est saisi dans ce dialogue. Le calcul ne présume pas de l’admissibilité
détaillée des revenus. La ligne 367 reste à zéro dans l’orchestrateur actuel.

Intégration : réduction unique de l’impôt Québec avec plancher zéro, avant les
crédits dividendes/étranger. Le crédit 391 est également transmis au plafond de
la ligne 396 (6C). Revenus, impôt fédéral et abattement restent inchangés.
Exemple synthétique : salaire 52 000 $, net Québec 50 095 $ → crédit 1 750 $.
Avec salaire 70 000 $ et net Québec recalculé 67 915 $, réduction 799,05 $,
crédit 950,95 $. À 81 500 $ de revenu net, le crédit est nul.

JSON : profil vide pour les anciens dossiers; types/clefs stricts, source et date
validées; inférence depuis l’estimation et refus des divergences; résultats
recalculés. GUI dédiée, confirmations révoquées après modification, réouverture
et effacement. Résumé, trace et PDF détaillent salaire, net, base, taux, réduction,
plafond fiscal, ligne 391, source et validation. Aucun envoi externe.

Validation ciblée 6D + régressions 6A/6B/6C : **226 passed, 5 warnings**.
Tests des seuils 7 500/20 000/56 500/81 500, âge 64/65, arrondis, plafond fiscal,
revenu net distinct du salaire, 391 dans 396, case 211, âge pensions contradictoire,
JSON ancien/nouveau/divergent, GUI, trace et PDF.
Journal précédent 6C : commit `0d091db`, 10 fichiers; suites complètes avant/après
commit **5843 passed, 8 warnings**; push réussi et dépôt propre avant 6D.

Journal 6D : suite complète avant commit **5903 passed, 8 warnings**
(`--capture=sys`, 187,05 s), diff sans erreur et PDF synthétique vérifié visuellement.


### Correction d'isolation des dossiers GUI après 6D

Défaut reproduit par un parcours réel : après activation du profil carrière
avec naissance et source propres au client A, « Initialiser le dossier fiscal »
pour le client B conservait ces données et leurs confirmations. L'audit de la
routine a identifié 23 profils omis : CELIAPP, déductions 4B–4F, profils fédéraux
familiaux et remboursables récents, intérêts étudiants fédéraux/Québec, achat
Québec, carrière Québec et profils de placement/crédit étranger.

La création réussie d'un nouveau dossier remet désormais ces profils à leur
état vide, comme les profils historiques. Une création refusée ne détruit pas
les données du dossier courant. Aucun calcul ni paramètre fiscal n'est modifié.
Les documents sélectionnés restent ceux de la préparation du nouveau dossier;
ce correctif concerne les faits et confirmations des profils, sans suppression
de fichiers. Le chargement d'un dossier existant conserve son propre contrat.

Validation ciblée : **46 passed, 5 warnings**, avec reproduction avant correction,
contrôle de la naissance/source/confirmations, absence de report étudiant hérité,
initialisation invalide et régressions GUI. La réinitialisation explicite devra
être complétée lors de tout ajout futur de profil.

Journal précédent 6D : commit `7a13915`, 10 fichiers; suites complètes avant et
après commit **5903 passed, 8 warnings**; push réussi et dépôt propre avant
cette correction indépendante.

Suite complète avant commit de la correction : **5906 passed, 8 warnings**,
`--capture=sys`, 200,23 s; `git diff --check` sans erreur.
