# POST-V1-B : programme et données utilisateur

Le tag v1.0.0 reste inchangé. Aucun calcul fiscal ni schéma fiscal n'est modifié.
Ce bloc prépare les chemins ; il ne produit ni exécutable ni installateur.

## Emplacements

Windows : `%LOCALAPPDATA%\ComptaPriveeAI`. Linux :
`$XDG_DATA_HOME/ComptaPriveeAI`, ou `~/.local/share/ComptaPriveeAI`.
Les chemins par défaut ne dépendent jamais du répertoire courant.
La racine utilisateur ne peut pas se trouver sous PROGRAM_DIR/RESOURCE_DIR.

- `data/comptaprivee.db` : comptabilité et journal d'audit.
- `data/dossiers_fiscaux/` : JSON fiscaux, identité conservée.
- `data/parametres.json`, `data/profil_comptable.json`, `data/logo_societe.*`.
- `data/ocr_review_queue.json` : file OCR.
- `exports/` : exports par défaut ; une destination explicite reste possible.
- `temp/` : temporaires OCR/conversion et validation de restauration.
- `logs/migration.log` : nombre de copies, sans nom ni montant client.

La résolution des ressources accepte le futur répertoire de bundle `_MEIPASS`.
Les fichiers distribués et les données utilisateur restent séparés. Le programme
ne crée aucun dossier utilisateur à l'import ; les écritures les créent au besoin.

## Migration explicite

Fermer toutes les instances et les outils accédant à l'ancienne base. Conserver
une sauvegarde et les pièces originales. Depuis les sources :

```powershell
.\.venv\Scripts\python.exe -m src.comptaprivee.main --migrate-data "C:\ancien-emplacement\comptaprivee-ai"
```

L'argument est la racine absolue contenant `data/`, pas `data/` lui-même.
La commande copie la base par snapshot SQLite, les paramètres, le profil, le logo,
la file OCR, les JSON fiscaux et les exports. Elle ne copie ni ne supprime les
documents originaux. Aucun parcours automatique ne recherche des dossiers clients.

Les sources ne sont jamais modifiées ni supprimées. Les copies fiscales conservent
les champs existants ; les références documentaires relatives deviennent absolues
vers l'ancienne racine et un ancien JSON sans case_id reçoit l'identifiant qu'il
avait lors de son chargement à cet ancien emplacement. Les case_id existants sont
conservés. Le formatage de la copie JSON peut donc changer, pas les montants.
Les références aux pièces d'origine restent valides tant que celles-ci restent en place.

Tous les conflits de contenu sont vérifiés avant copie des données. Une destination
différente provoque un refus explicite : résoudre manuellement, ne pas écraser.
Relancer la migration sans changement est idempotent. Après modification du dossier
dans l'application, une nouvelle migration de l'ancienne copie peut légitimement
être refusée. Une interruption laisse au plus des copies complètes déjà publiées ;
la commande peut être reprise. La publication exclusive utilise des liens physiques
sur le volume utilisateur : un système de fichiers ne les supportant pas provoque
une erreur sans écrasement. Aucun dossier de secours n'est supprimé par la migration.

## Sauvegarde, restauration et temporaires

Les noms internes des anciennes archives `data/...` restent compatibles. Leur
allowlist est inchangée : base, paramètres, profil et dossiers fiscaux seulement.
Exports, logo, file OCR, documents originaux, code et temporaires restent exclus.
Les sources absolues sont classées par leur chemin relatif à la racine utilisateur,
jamais en supposant qu'un chemin absolu est nécessairement un JSON fiscal.

La restauration refuse une racine différente de USER_DATA_DIR. Les contrôles
existants de manifeste, hash, contenu, case_id, liens et rollback sont conservés.
Le staging de sauvegarde reste près de la destination ; celui de remplacement
reste sur le volume utilisateur. Les temporaires normaux sont nettoyés à la sortie.
Un arrêt brutal peut laisser des fichiers ; aucun service de nettoyage n'est ajouté.

Les données restent non chiffrées. Une restauration et une migration s'effectuent
instances fermées. Le snapshot/migration n'est pas une synchronisation multi-postes.

## Validation locale POST-V1-B

Les groupes ciblés couvrent stockage, exports, migration, sauvegarde/restauration,
OCR et GUI Windows avec `--capture=sys`. Dernier groupe ciblé : 78 tests réussis.
Suite complète locale unique : **7 512 passed, 5 warnings**, en 270,06 secondes.
Les 11 nouveaux cas du module de chemins sont aussi ajoutés à la CI Windows.
Les résultats CI du commit publié sont à relever dans le checkpoint de session.
Aucune migration de données réelles n'a été exécutée pour cette validation.
