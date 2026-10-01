# Prototype Windows onedir — POST-V1-C

État POST-V1-C : build réussi, validation runtime **incomplète**.
La reprise POST-V1-C2 ci-dessous contient les résultats les plus récents.
Ne pas distribuer ce prototype ni commencer l'installateur sur cette seule preuve.
Le tag stable v1.0.0 reste inchangé. Aucun moteur fiscal n'est modifié.

## Construire

Depuis la racine du dépôt, Windows x64, Python 3.12 :

```powershell
py -3.12 -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requirements-build.txt
.\scripts\build_windows.ps1
```

Le script refuse d'écraser un bundle existant. Pour une nouvelle tentative :

```powershell
.\scripts\build_windows.ps1 -Destination 'dist/prototype-suivant'
.\scripts\check_windows_bundle.ps1 -Bundle 'dist/prototype-suivant/ComptaPriveeAI'
```

PyInstaller 6.22.3 et hooks-contrib 2026.8 sont épinglés, ainsi que les
dépendances directes de requirements.txt. Les dépendances transitives ne sont
pas toutes verrouillées : procédure répétable, pas garantie de build identique
octet pour octet. Environnement audité : Python 3.12.10, lxml 6.1.3.
Référence : <https://pyinstaller.org/en/latest/spec-files.html>.

## Configuration

`ComptaPriveeAI.spec` produit un dossier sans console, sans UPX. Le lanceur
appelle `src.comptaprivee.gui.lancer_interface()` sans dupliquer la GUI.
Les échecs normaux écrivent uniquement le type d'exception dans
`%LOCALAPPDATA%\ComptaPriveeAI\logs\startup.log`, puis affichent un dialogue.

Hidden imports : docx, lxml.etree, PIL.ImageTk, win32com.client, pythoncom,
pywintypes, openpyxl. Collecte explicite des modèles python-docx et des DLL
PyMuPDF ; hooks standards Tk/Tcl, Pillow, docx/lxml, openpyxl et pywin32.
Aucun hook personnalisé. Les ressources sont sous `_internal` via RESOURCE_DIR.
Les DLL comprennent python312, tcl86t, tk86t, sqlite3, mupdfcpp64,
pythoncom312, pywintypes312, VCRUNTIME140, libcrypto/libssl et libffi.
Tesseract, Word et Excel restent externes. Aucun téléchargement automatique.

Le diagnostic embarqué `--prototype-check` exige une variable explicite et
refuse un profil non vide sans marqueur fictif. Le script PowerShell crée un
profil dédié sous `tmp/`, substitue LOCALAPPDATA, retire Python/Tesseract du
PATH et lance directement l'exe depuis C:\Windows. Il prévoit trois passages,
dont un avec Tesseract s'il est accessible, et compare les empreintes du bundle.
La trace détaillée d'échec est réservée au profil marqué fictif.

## Résultats observés et limites

- Build initial et révisions r2/r3 réussis. Dernier exe :
  `dist/prototype-r3/ComptaPriveeAI/ComptaPriveeAI.exe`.
- r3 : 1 016 fichiers, 100 958 109 octets, environ 96,28 Mio.
- Premiers passages r1/r2 : exe direct, chemin avec espaces et accents,
  cwd C:\Windows, Python absent du PATH. Ce n'est pas une VM sans Python installé.
- Parcours fictif initial réussi : Tkinter/agent fiscal, paramètres, SQLite,
  sauvegarde/rechargement JSON, estimation 2025, PDF lu par PyMuPDF, CSV,
  modèle DOCX, XLSX, sauvegarde et restauration. Les données sont dans le
  LOCALAPPDATA substitué ; ressources et modules viennent du bundle.
- Temps r2 : parcours complet 4,19 s, création GUI 0,587 s. Ce dernier chiffre
  n'inclut pas le démarrage du bootloader ni tous les imports.
- Sans Tesseract : message clair, extraction PDF textuel fonctionnelle.
  Tesseract est installé sur le poste ; OCR fra+eng dans le bundle reste à valider.
- pywin32 chargé ; absence Office simulée par échec COM, message de prérequis
  vérifié au premier passage r2. Word/Excel sont présents sur le poste :
  absence réelle sur machine propre et conversion COM réelle non validées.
- Deuxième passage r2 : `PermissionError`, code sortie 1. Les exports ont été
  régénérés, mais la persistance complète après relancement n'est pas validée.
  Une exécution source sur le même profil réussit ; cela ne prouve pas le
  fonctionnement frozen. Le fichier en cause n'a pas encore été identifié.
- r3 ajoute une trace de diagnostic détaillée pour identifier cet échec.
  Son lancement est bloqué avant Python par Windows :
  « An Application Control policy has blocked this file. »
  Aucune protection n'a été désactivée ou contournée. Résoudre ce blocage dans
  un environnement de test autorisé avant de reprendre le diagnostic.
- Le contrôle final des empreintes après les trois passages n'est pas atteint.
  Ne pas considérer l'absence d'écriture dans le bundle comme entièrement validée.

## Inventaire et warnings

Inventaire r3 : aucun fichier JSON/DB/PDF/CSV/XLSX, .env, dépôt Git,
répertoire tests/fixtures/exports utilisateur détecté ; aucun pytest/tests
dans la table de modules PYZ. `base_library.zip` et les modèles DOCX distribués
par python-docx sont des ressources légitimes. Recherche de signatures usuelles
de jetons GitHub et clés privées dans les ressources texte : zéro candidat.
Ce contrôle n'est pas une certification exhaustive de secrets dans les binaires.
Le spec ne collecte aucun dossier utilisateur ni la racine entière du dépôt.
`dist/`, `build/`, `.venv-build/`, journaux et profils fictifs restent ignorés.

Les warnings PyInstaller concernent notamment les modules POSIX non applicables,
les imports conditionnels, win32com.gen_py et des options non utilisées ici :
numpy, pandas, fontTools, olefile, defusedxml, parsers HTML lxml.
Aucune DLL manquante signalée dans le build ; tous les formats optionnels ne
sont pas validés. Voir `build/ComptaPriveeAI/warn-ComptaPriveeAI.txt` local.

## Validation source et suite

```powershell
.\.venv\Scripts\python.exe -m pytest --capture=sys -q tests/test_windows_launcher.py tests/test_document_converter.py tests/test_app_paths.py tests/test_release_platform.py --tb=short
```

Résultat final : **69 passed, 5 warnings** (dépréciations SWIG/PyMuPDF).
`git diff --check` propre. Aucun calcul fiscal modifié.
Full suite et publication différées : validation du bundle bloquée, aucun
commit/push de ce travail. Les CI précédentes ne valident pas ces changements.

À la fin de POST-V1-C, avant POST-V1-D : diagnostiquer le second passage, réussir les trois passages
sur un environnement autorisé, vérifier le lancement GUI normal interactif,
tester une machine propre sans Python/Office et l'OCR présent, puis full suite,
revue source, commit/push et CI Linux/Windows. Aucun installateur créé.

## Reprise POST-V1-C2 — 1er octobre 2026

### Deux refus de fichiers distincts, sans attribution abusive

Un défaut SQLite est démontré en source : désactiver le GC, appeler
`initialiser_base()`, créer une sauvegarde puis la restaurer provoque :

```text
backup_manager.py, restaurer_sauvegarde, os.replace(..., cible)
PermissionError: [WinError 5] Access is denied:
.../Diagnostic C2 été SQLite/.restore-0xmwgpvn/nouveau-0
 -> .../Diagnostic C2 été SQLite/data/comptaprivee.db
```

La connexion encore ouverte empêche le remplacement du fichier. La restauration
réussit après libération par GC. Correction bornée : `contextlib.closing` autour
des connexions utilisées par database.py et audit_log.py, avec conservation du
contexte transactionnel SQLite (commit/rollback avant fermeture). L'API
`ouvrir_connexion` reste inchangée. Aucune DB supprimée, aucun retry ajouté.
Les tests retiennent volontairement les connexions pour exclure une fermeture
accidentelle par GC et vérifient la restauration ainsi que la fermeture explicite.
Des processus enfants simulent un arrêt brutal avec transaction non validée en
modes DELETE et WAL : les données validées restent disponibles après reprise.

**Ce défaut n'est pas une preuve de la cause historique du refus r2.** Le seul
nouveau build C2, qui inclut la correction, a capturé un autre refus exact :

```text
scripts/prototype_check.py:10 run -> :121 _run
src/comptaprivee/backup_manager.py:135 creer_sauvegarde
PermissionError: [WinError 5] Access is denied:
C:/projects/comptaprivee-ai/tmp/Prototype été 20261001-094207/Profil fictif/ComptaPriveeAI/.backup-x90fqra5/sauvegarde.zip
 -> C:/projects/comptaprivee-ai/tmp/Prototype été 20261001-094207/Profil fictif/ComptaPriveeAI/prototype.zip
```

Il s'agit du remplacement atomique de l'archive existante, **avant** la
restauration. L'attribut est Archive, pas ReadOnly ; propriétaire utilisateur,
ACL OWNER RIGHTS FullControl. Aucun processus ComptaPriveeAI résiduel observé.
Le détenteur d'un éventuel verrou au moment exact du refus n'a pas été capturé.
Ne pas attribuer ce refus à Defender, SQLite, Tk ou PyMuPDF sans preuve.
Aucune modification des ACL ni de la sauvegarde pour masquer cette erreur.

### Relancements, fichiers et OCR

- Ancien r2 : trois passages successifs réussis sur un nouveau profil fictif.
- C2 : passage 1 réussi (sans OCR), passage 2 refus d'archive ci-dessus, puis
  passages 3, 4 et 5 réussis sur **le même** profil, sans suppression ni réparation.
  JSON conservé, même case_id, sauvegarde/restauration réussies, OCR fra+eng OK.
- Chemin avec espaces et accents ; exe direct depuis C:\Windows. Les trois
  derniers passages utilisent le PATH normal pour rendre Tesseract accessible.
- Après sortie, ouverture exclusive en lecture des 14 fichiers du profil :
  zéro refus. Répertoire temp vide, aucun staging .backup/.restore résiduel.
- Inventaires SHA-256 du bundle original et de la copie exécutée identiques
  après ces passages : aucune écriture constatée dans le bundle.
- Journal de démarrage testé trois fois sur profil fictif, trois entrées,
  ouverture exclusive possible ensuite ; aucun handler persistant.
- Audit du parcours : PDF/PyMuPDF, CSV, JSON et ZIP fermés par contexte ou
  finally ; staging/temp nettoyés ; Tk détruit en finally. Office absent simulé,
  aucune instance COM réelle ouverte pendant le diagnostic. Une vérification
  COM réelle reste distincte de cette preuve.

### Windows Application Control

Les événements CodeIntegrity du 1er octobre à 09:22:09 (3033, 3077, 3089, 3118)
visent `tmp/Prototype été 20261001-092205/ComptaPriveeAI/ComptaPriveeAI.exe`
(r3). Ils indiquent les exigences de signature et Smart App Control ; politique
`{0283ac0f-fff1-49ae-ada1-8a933130cad6}`. Message au lancement :
« An Application Control policy has blocked this file. »

r1, r2, r3 et C2 sont NotSigned. r2 et C2 fonctionnent actuellement ; r1 avait
fonctionné lors de POST-V1-C. r3 n'a pas été déplacé ni relancé pour essayer de
contourner le blocage. R2/r3 diffèrent par l'exe et base_library.zip ; les autres
ressources sont identiques. Une décision de confiance/signature propre à
l'artefact est plausible, mais la dépendance au répertoire n'est pas démontrée.
Aucune politique ni protection système modifiée.

### Construction et validation

Une seule reconstruction C2 : `dist/prototype-c2/ComptaPriveeAI/ComptaPriveeAI.exe`,
100 958 633 octets pour le bundle. SHA-256 de l'exe :
`e79433dd8962bfbe3dbf0828afcb9fc62d70b8c4664fdd9dc83adbe53abfc49f`.
Le script utilise maintenant un workpath unique sous build/ : analyse neuve,
aucun cache/staging précédent supprimé, destination existante toujours refusée.
Il ne remplace donc pas un bundle en cours d'utilisation.

Tests ciblés : 85 passed, 5 warnings. Le test ajouté couvre SQLite et les
arrêts brutaux ; il est inclus dans le job CI Windows. La publication du code
de diagnostic ne constitue pas une validation pour distribution du binaire.
Le refus transitoire de remplacement ZIP demeure ouvert : **NO-GO installateur**.

Suite complète locale unique : **7 521 passed, 5 warnings**, 293,54 s, avec
`--capture=sys`. `git diff --check` propre. Inventaire du build C2 : aucun
fichier client ou test détecté, zéro signature de secret dans les ressources
texte examinées (mêmes limites d'inspection que ci-dessus). Aucun artefact
généré destiné au commit. La CI doit être évaluée sur le commit publié.

## POST-V1-C3 — remplacement de prototype.zip

### Opération exacte et audit

`scripts/prototype_check.py` appelle `creer_sauvegarde(root / 'prototype.zip')`.
Cette fonction crée un répertoire unique `.backup-*` dans le parent de la
destination, écrit `sauvegarde.zip` avec `with ZipFile(..., 'w')`, ferme le ZIP,
puis appelle `os.replace(archive_temp, destination)`. La destination existe
au second passage. Elle n'est jamais supprimée avant le remplacement.
Les sources JSON sont lues par read_bytes/copyfile ; les snapshots SQLite
utilisent closing. La restauration ferme aussi son ZipFile avant remplacement
des données. Aucun lecteur antivirus simulé n'existe dans ce parcours.

Le test de fermeture retient les objets ZipFile et vérifie `fp is None` au
moment du remplacement : sa réussite ne dépend pas du ramasse-miettes.
Le remplacement Windows réel est exercé par ces tests. La stratégie ne promet
pas une durabilité face à une panne électrique ; aucun fsync supplémentaire
n'est ajouté pour résoudre un refus de permission sans rapport démontré.

### Reproduction et classification C

Avant correction, 30 créations/remplacements en source ont réussi : 10 par
chemin (normal, espaces, Unicode), dont création initiale puis même destination.
Un script local prévoyait timestamp, traceback, chemins, existence, taille,
lecture immédiate et interrogation Windows Restart Manager sur tout refus.
Aucun outil tiers n'a été téléchargé ; handle.exe n'était pas disponible.

Le seul build C3 a ensuite reproduit le refus malgré les tentatives bornées :

```text
2026-10-01T13:59:42.346500+00:00
prototype_check._run -> creer_sauvegarde -> _remplacer_archive -> os.replace
PermissionError: [WinError 5] Access is denied:
.../Prototype été 20261001-095932/Profil fictif/ComptaPriveeAI/.backup-wc5l92ru/sauvegarde.zip
 -> .../Prototype été 20261001-095932/Profil fictif/ComptaPriveeAI/prototype.zip
```

L'archive existante fait 8 182 octets et n'est pas ReadOnly. Une deuxième
séquence surveillée, même build et nouveau profil `tmp/C3 surveillé été`, donne :

| Passage | Heure locale | Résultat | Archive existante | Lecture immédiate | Restart Manager |
| --- | --- | --- | --- | --- | --- |
| 1 | 10:01:51.701957 | succès | 8 162 octets | OK | aucun propriétaire observé |
| 2 | 10:01:54.122253 | WinError 5, replace ZIP | 8 162 octets | OK | aucun propriétaire observé |
| 3 | 10:01:56.449199 | WinError 5, replace ZIP | 8 162 octets | OK | aucun propriétaire observé |

Restart Manager a été interrogé pendant les processus à intervalles de 100 ms
et après les refus. Une absence de résultat n'exclut pas un filtre système ou
un handle trop bref/non exposé. **Classification C : propriétaire non identifié**.
Ni antivirus, ni indexeur, ni handle applicatif ne sont désignés comme cause.

Sans réparation de fichier, trois relancements suivants avec PATH normal
réussissent, chacun avec trois écritures et vérification ZIP, restauration et
OCR fra+eng. Puis PATH réduit → normal → réduit réussit également, sur le même
profil et même binaire. La causalité du PATH n'est donc pas démontrée.
Le caractère non permanent du refus est observé ; sa durée et sa cause restent
inconnues. Ne pas présenter les succès tardifs comme correction de sa cause.

### Reprise bornée et garanties

`_remplacer_archive` limite `os.replace` à quatre appels, avec attentes de
50, 100 et 200 ms (350 ms cumulés), uniquement sur PermissionError. Aucune
reconstruction du ZIP entre tentatives, aucun unlink de l'archive précédente,
aucune modification de droits ou de sécurité. Les autres exceptions remontent
immédiatement ; le quatrième PermissionError remonte sans être remplacé.
La reprise améliore la tolérance à un refus bref mais **ne résout pas tous les
refus observés dans ce poste**. Aucun allongement empirique des délais effectué.

Les tests démontrent la préservation de l'ancienne archive si le refus persiste,
la lisibilité du nouveau ZIP, l'erreur finale exacte et le nettoyage du staging.
Le diagnostic embarqué produit maintenant trois ZIP successifs par lancement.

### Validation et décision

- 75 tests ciblés verts, 5 warnings ; nouveaux tests inclus dans la CI Windows.
- Une full suite locale : **7 528 passed, 5 warnings**, 294,85 s.
- Une reconstruction : `dist/prototype-c3/ComptaPriveeAI/ComptaPriveeAI.exe`.
- C3 s'exécute sans blocage Application Control ; le refus ZIP est dans Python,
  distinct du blocage pré-exécution r3. Aucune politique système modifiée.
- Neuf écritures ZIP réussies sur trois relancements tardifs, puis neuf autres
  lors de la comparaison PATH ; profil LOCALAPPDATA fictif conservé.
- Les deux premières séquences comportent toutefois les échecs indiqués plus
  haut : le parcours automatisé complet n'est pas déclaré systématiquement vert.
- Inventaire SHA-256 identique entre le build et la copie exécutée (1 016
  fichiers), temporaires et staging nettoyés ; aucun artefact binaire suivi.

**POST-V1-D : NO-GO.** Avant installateur, capturer la décision native de refus
sur une reproduction (outillage système de traçage de fichiers à organiser),
ou confirmer le comportement dans un environnement Windows de test autorisé.
Ne pas contourner la sécurité, augmenter indéfiniment les délais, ou déclarer
un responsable sans preuve. Le commit de la reprise bornée et des diagnostics
n'est pas une validation de distribution du binaire.

## POST-V1-C4 — acceptation fonctionnelle du refus Windows

Cette décision remplace le NO-GO C3 pour la préparation de POST-V1-D : le refus
environnemental non expliqué est accepté comme **P2**, sous réserve du maintien
des garanties ci-dessous. Il n'est pas présenté comme un verrou identifié ou
comme un problème définitivement corrigé.

### Message et comportement GUI

Le bouton réel « Créer une sauvegarde... » intercepte maintenant PermissionError
avant le gestionnaire générique. Il affiche :

> Windows refuse l'accès à un fichier nécessaire à la sauvegarde.
>
> Si le remplacement a été refusé, la sauvegarde précédente a été conservée.
>
> Fermez tout programme utilisant ce fichier puis réessayez, ou choisissez un
> autre nom de fichier.

Le statut devient « Sauvegarde non confirmée — réessayez ou choisissez un autre
nom ». Aucun traceback, nom de temporaire ou message d'exception brut n'est
affiché pour ce refus. La formulation conditionnelle couvre aussi un refus
avant l'étape de remplacement, sans affirmer qu'un verrou a été identifié.
Le retry reste inchangé : quatre tentatives, attentes cumulées de 350 ms.
Une sauvegarde normale réussie au premier essai n'attend pas ces délais.

### Acceptation déterministe sur la vraie GUI Tk

`tests/test_gui_backup_acceptance.py` ouvre les paramètres et invoque le vrai
bouton, avec données exclusivement fictives. Seul os.replace vers prototype.zip
est configuré pour refuser systématiquement :

- quatre tentatives, puis un seul message d'erreur propre, aucun succès annoncé ;
- ancienne archive et JSON fiscal identiques octet par octet ;
- aucun staging .backup-* restant ou présenté comme sauvegarde ;
- le même bouton crée immédiatement `prototype-2 été.zip`, tandis que le refus
  reste actif sur l'ancien nom ; ZIP lisible, JSON fiscal identique dans l'archive ;
- le nom initial peut être réessayé avec succès après libération du refus ;
- Tk reste actif, sans exception non traitée de callback.

Les tests C3 continuent de couvrir le refus transitoire suivi de succès et
l'erreur permanente finale. Le test C4 fait partie de la CI Windows.

### Parcours du bundle autorisé existant

Aucune reconstruction en C4. Le bundle C3 a été lancé directement depuis
C:\Windows, avec LOCALAPPDATA substitué vers `tmp/C4 GUI fictif`, puis piloté
par ses contrôles GUI Windows. Les premières archives `prototype.zip` et
`prototype-2.zip` sont lisibles ; ce profil initialement vide ne contient alors
que le manifeste. Le dialogue confirme une restauration de zéro fichier,
puis l'application se ferme normalement.

Après préparation d'une base SQLite et d'un dossier fiscal synthétique, le
même bundle est relancé sur ce profil. La GUI crée `prototype-3.zip` sous un
nouveau nom. L'archive contient la DB et le JSON fiscal, comparé octet par octet
au fichier source. Fermeture normale et inventaire SHA-256 du bundle inchangé.
Les contrôles de refus permanent et du **nouveau message** concernent la GUI
source testée : C3 conserve son ancien message. Le build préparé pour
POST-V1-D devra inclure le commit C4 avant toute distribution.

Le pilote Windows de diagnostic a nécessité des adaptations aux dialogues
natifs (focus et identifiants de boutons) ; ses scripts et captures fictives
restent dans tmp/, hors Git. Ces limites d'automatisation ne sont pas des
erreurs du moteur de sauvegarde.

### Résultats et décision

51 tests ciblés réussis, 5 warnings. Une full suite locale : **7 529 passed,
5 warnings**, 291,34 s, avec `--capture=sys`. `git diff --check` propre.
Aucun changement fiscal, de sécurité Windows, de tag ou de retry.

**GO pour préparer POST-V1-D**, après CI verte du commit C4. Ce GO accepte le
refus permanent lorsqu'il est signalé proprement, préserve les données et
laisse disponible la sauvegarde sous un nouveau nom. Il ne garantit pas
l'absence de refus Windows et ne valide pas une distribution de l'ancien C3.
Aucun installateur créé pendant cette session.
