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

Le Bloc 2D n'est pas commencé; il nécessite un nouvel accord utilisateur.
