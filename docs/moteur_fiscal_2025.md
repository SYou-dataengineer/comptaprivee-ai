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
| Québec | Cotisations professionnelles, personne vivant seule, âge/retraite, assurance médicaments, excédents RRQ/AE/RQAP | Annexe B combinée non prise en charge; assurance médicaments limitée à certains profils |
| Pensions | Fonctions de calcul de crédits présentes | La ligne fédérale 31400 est explicitement bloquée dans l'orchestrateur : les revenus de pension ne sont pas encore intégrés; présence du module ≠ prise en charge d'un retraité |
| Chaîne applicative | Validation humaine, dossier verrouillé, sauvegarde JSON/rechargement, résumé, trace et PDF, tests Tkinter | L'extraction initiale concerne les cases reconnues du T4/RL-1; les autres feuillets nécessitent de futurs blocs |

Fichiers de référence : `tax_engine_input_2025.py`, `tax_income_2025.py`,
`tax_estimation_2025.py`, `tax_reconciliation_2025.py`, `tax_*_2025.py`,
`tax_field_extractor.py`, `tax_case_storage.py` et leurs tests.

## Principaux manques et ordre proposé

Chaque ligne représente une famille à découper en blocs vérifiables. Arrêt
après chaque bloc pour bilan et accord utilisateur; aucune suite automatique.

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
| **3A — intérêts canadiens sur feuillets** | Une paire T5 13/RL-3 D, CAD, titulaire unique; 12100/130 et FSS | Extraction, validation des pièces et du profil, GUI, JSON, résumé, trace, PDF; seul bloc implémenté maintenant |
| 3B — intérêts sans feuillet et autres intérêts documentés | Relevés bancaires, impôt remboursé, CPG courus; T3/RL-16 après ventilation | Identifiants des sources, déduplication avec 3A, échéanciers, intérêts déjà déclarés; attribution et devises restent exclus jusqu'à couverture |
| 3C — dividendes canadiens | Déterminés/autres; T5/RL-3 puis T3/RL-16; majorations, crédits fédéral/Québec | Ordre des crédits et abattement, revenu net majoré, FSS, refus TOSI/cas particuliers; conservation des revenus réels et imposables |
| 3D — dispositions et distributions en capital | Annexe 3/G, T5008/RL-18, T3/RL-16 et T5/RL-3 | PBR prouvé, frais, historique, pertes apparentes, taux 2025; différencier revenu d'entreprise et capital, contrôler impôt minimum |
| 3E — frais de placement et annexe N | 22100/231, 260/276, reports 252 | Utilisation des emprunts, frais admissibles, revenus de placement des blocs précédents, soldes distincts; aucune double déduction de frais de transaction |
| 3F — reports de pertes en capital | 25300/290, T1A/TP-1012.A, TP-729, soldes historiques | 3D et 3E; taux d'origine, avis de cotisation, ordre d'utilisation, plafonds et non-double consommation |
| 3G — placements et impôts étrangers | Revenus bruts/devises, T2209/40500, TP-772/409, déclarations de biens étrangers | Pays, convention, limites de crédit et déductions connexes; pas de conversion ou crédit implicites |
| 3H — combinaisons contrôlées | Plusieurs sources, placements + retraite/remplacement | Assiette FSS globale, récupérations AE/PSV, crédits/annexe B/RAMQ recalculés; validation de chaque combinaison avant ouverture |

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
Les garde-fous historiques demeurent, notamment le refus du calcul global
au-delà de 129 590 $ de revenu imposable Québec dans le parcours actuel
des crédits. Le barème FSS est testé séparément jusqu'à son plafond.

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
refusé. Les Blocs 3B à 3H restent non implémentés.

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
Les garde-fous du moteur global sur crédits, RAMQ et revenus élevés
(notamment 129 590 $ de revenu imposable Québec) restent en vigueur.
Les dividendes et tous les blocs 3C à 3H restent à construire.

Suite complète finale `python -m pytest -q` : **2 560 tests réussis**,
8 avertissements de dépréciation existants, aucun échec (82,03 s en local).
