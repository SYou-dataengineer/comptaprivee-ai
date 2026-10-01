# POST-V1-E — validation de distribution Windows

Audit du 1er octobre 2026, départ propre sur f9a7fe6. Aucune modification
applicative, de version, de tag ou de politique Windows. Aucun installateur
diffusé, aucune GitHub Release créée.

## Référence conservée

`dist/installer-1.0.0/ComptaPriveeAI-Setup-1.0.0.exe`, 35 406 324 octets :

`4F16FD69CA6C29D91366099F3ABE6843352268E5973ED53AF6AA9245A7F94F6D`

Hash vérifié au début et après les contrôles. Le programme déjà installé sous
Program Files correspond toujours aux 1 016 fichiers du bundle de cette
référence ; les deux seuls fichiers supplémentaires sont ceux du désinstalleur.

## Machine indépendante : non validée

Le poste utilisé est Windows 11 Pro, 10.0.26200, avec Python, Git, dépôt source,
Tesseract et Office présents. WindowsSandbox.exe est absent. Les services
Hyper-V sont actifs, mais Get-VM refuse la lecture dans le contexte accessible.
Une tentative d'inventaire en lecture seule via élévation Windows standard
termine avec code 1 sans fournir de liste exploitable. Aucun réglage système
n'est modifié pour passer ce refus.

**Aucune VM propre ou autre machine indépendante n'a été rendue accessible ni
validée pendant cette session.** Cela ne signifie pas qu'aucune VM n'existe.
Il manque une machine de test autorisée, un Windows propre sans Python/Git,
sans dépôt/.venv, et les preuves d'installation puis du parcours complet sur
cette machine. Le retrait d'outils du PATH n'est pas une preuve de leur absence.

## Contrôles locaux E et preuves antérieures D

| Point | Preuve et limite |
| --- | --- |
| Installation Program Files, raccourcis, désinstallation/réinstallation | validés sur ce même poste en POST-V1-D, non rejoués comme prétendue installation indépendante |
| Premier lancement E | profil fictif neuf `tmp/POST-V1-E sans outils`, USER_DATA_DIR créé par l'application |
| Sans Python/Git/Tesseract dans PATH | Get-Command ne trouve aucun des trois ; exe installé lancé directement, cwd C:\Windows, PYTHONHOME/PYTHONPATH vides |
| Parcours principal | diagnostic embarqué : Tk, faits fiscaux synthétiques 2025, PDF textuel, calcul, PDF, CSV, trois ZIP et restauration ; pas une nouvelle validation manuelle de chaque écran d'import |
| Relancement | même case_id fictif, JSON retrouvé, diagnostic réussi |
| OCR sans Tesseract accessible | message de prérequis clair, GUI et PDF textuel fonctionnels |
| OCR avec PATH normal | fra+eng réussi dans l'exe installé |
| Données conservées à désinstallation | comparaison d'empreintes réalisée en D ; cette preuve reste locale |
| Écriture dans Program Files | fichiers du payload identiques après les parcours E |

Le `--prototype-check` génère exclusivement des données fictives dans un profil
explicitement marqué. Il exerce le moteur avec des faits validés synthétiques,
pas une validation comptable réelle. Aucun client réel utilisé.

## Office : résultat réel et anomalie

L'absence d'Office est simulée par le diagnostic du bundle ; une machine sans
Office n'a pas été testée. En complément, les fonctions de conversion **source
inchangées au commit f9a7fe6** ont été appelées avec Word/Excel réellement
installés via COM. Il ne s'agit pas d'un test de ces conversions via la GUI
du bundle :

- Word : document fictif converti, PDF d'une page, texte attendu conservé.
- Excel : classeur contenant `DOCUMENT FICTIF POST V1 E` en A1 et `123.45` en
  B2 ; conversion produisant une page, mais texte PDF extrait égal à `123.45`
  seulement. Le contrôle exigeant aussi l'intitulé échoue.

Le code de recherche de la première cellule commence après A1, puis utilise
le résultat pour définir PrintArea. Ce point est une piste concrète à corriger
dans une session dédiée avec régression A1, pas une correction faite ici.
Les documents et sorties fictifs restent dans `tmp/POST-V1-E Office fictif`.
Ne pas présenter la conversion Excel comme validée intégralement. Aucune
instance Office créée par ce contrôle n'est volontairement laissée ouverte.

## Reproductibilité depuis source propre

Checkout détaché créé dans `tmp/post-v1-e-source`, HEAD
`f9a7fe64a87ff770839d444ebf38a907c833ec53`, état Git vide avant et après build.
Chaîne rejouée avec les scripts suivis :

```powershell
.\scripts\build_windows.ps1 -Python 'C:\projects\comptaprivee-ai\.venv-build\Scripts\python.exe' -Destination 'dist/reproduction'
.\scripts\build_installer.ps1 -Bundle 'dist/reproduction/ComptaPriveeAI' -ISCC 'C:\projects\comptaprivee-ai\build\tools\inno-6.7.3\ISCC.exe' -Destination 'dist/installer-reproduction'
```

Ces commandes sont lancées depuis la copie propre. L'environnement de build
préexistant est réutilisé : ce n'est pas une réinstallation indépendante des
outils. Versions relevées : Python 3.12.10, PyInstaller 6.22.3,
hooks-contrib 2026.8, Inno Setup 6.7.3, PyMuPDF 1.26.4, Pillow 11.3.0,
openpyxl 3.1.5, python-docx 1.2.0, lxml 6.1.3, pywin32 311.

Les deux compilations réussissent. Artefact **distinct, non installé et non
substitué à la référence** :

- `tmp/post-v1-e-source/dist/installer-reproduction/ComptaPriveeAI-Setup-1.0.0.exe`
- 35 407 251 octets ; build UTC 2026-10-01T15:33:52.1623351Z.
- SHA-256 : `A859C5F5C66469150EA2838C91BAE8D83323A1FB46B901AE0C79232EFE0746C0`.

La différence d'empreinte est attendue pour une chaîne ne garantissant pas
l'identité binaire (chemins de compilation, horodatages et archives). La cause
octet par octet n'est pas auditée. La référence conserve son hash imposé.

## Métadonnées, Windows et inspection

| Propriété Windows | Installateur de référence | ComptaPriveeAI.exe installé |
| --- | --- | --- |
| ProductName | ComptaPrivée AI | vide |
| ProductVersion | 1.0.0 | vide |
| FileVersion (texte) | vide | vide |
| FileVersion numérique | 0.0.0.0 | 0.0.0.0 |
| CompanyName | ComptaPrivée AI | vide |
| Signature | NotSigned | NotSigned |

Les noms de fichiers sont conformes. Le Publisher est un libellé neutre du
produit, pas une société légale validée. Aucune icône finale .ico n'existe dans
le projet ; les icônes standard restent utilisées. Les ressources de version
Windows doivent être finalisées avant diffusion publique, sans les présenter
comme déjà correctes parce que ProductVersion de Setup vaut 1.0.0.

Aucun blocage SmartScreen/WDAC observé sur ces parcours locaux. Aucun flux
Zone.Identifier trouvé sur l'installateur local : un scénario de téléchargement
Internet et sa réputation SmartScreen ne sont pas validés. Aucune protection
n'a été désactivée. Les avertissements éventuels sur une autre machine restent
à relever séparément pour Setup et pour l'application ; leur possibilité de
continuer n'est pas connue ici.

Inspection renouvelée du contenu installé : aucune DB, JSON, PDF, CSV, XLSX
client, backup réel, .env, .git ou module tests/pytest détecté. Aucun jeton
GitHub ou en-tête de clé privée parmi les signatures recherchées dans les
ressources texte. Ce contrôle limité ne certifie pas tous les binaires tiers.

## Suite à réaliser et décision

Le [guide utilisateur Windows](guide_windows.md) couvre installation, données,
sauvegarde, OCR, Office facultatif, désinstallation, limites 2025 et absence de
signature. Les preuves de D restent dans [installateur_windows.md](installateur_windows.md).

Sur une machine indépendante autorisée, relever : Windows exact, absence de
Python/Git/repo, hash de référence, messages de sécurité sans contournement,
installation, raccourcis, création du profil, import et validation manuels d'un
PDF fictif, calcul, exports, sauvegarde, relancement, restauration,
désinstallation avec empreintes préservées, réinstallation. Tester si possible
Office réellement absent et Tesseract absent puis présent, sans téléchargement
automatique par l'application.

**NO-GO distribution contrôlée selon les critères E** : installation indépendante
non validée, parcours manuel complet sur machine propre manquant, anomalie
Excel ouverte. Le GO local D ne constituait pas cette validation indépendante.

**NO-GO public** : signature/acceptation explicite du risque non traitée,
Publisher et icône non finalisés, métadonnées Windows incomplètes, documents
commerciaux restant à valider. Aucune décision d'acceptation de risque n'est
prise à la place de l'utilisateur. Aucune nouvelle version ni Release.
