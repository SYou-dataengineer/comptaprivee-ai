# ComptaPrivée AI 1.0.0 — guide Windows de test

Cette version prépare des dossiers fiscaux **2025 uniquement**. Elle n'est pas
encore validée pour une distribution publique. Utilisez exclusivement des
données fictives pour les essais de cette version.

## Installer et démarrer

1. Recevez l'installateur `ComptaPriveeAI-Setup-1.0.0.exe` par le canal de test
   convenu. Vérifiez son empreinte dans PowerShell :

   ```powershell
   Get-FileHash .\ComptaPriveeAI-Setup-1.0.0.exe -Algorithm SHA256
   ```

   Référence attendue :
   `21395771EB35FA6274E7E5160F8DF0E4205C29186815CEB7E7397B85DEFACD33`.
   Cette référence POST-V1-E3 provient du commit
   `ca6012e5080bb80083f57d6365bfe113fda96150` et intègre la correction Excel.
   Si elle diffère, arrêtez l'installation et signalez la différence.
2. Lancez l'installateur. L'installation pour tous les utilisateurs dans
   Program Files demande l'autorisation administrateur Windows.
3. Le raccourci Menu Démarrer est créé ; celui du Bureau est facultatif.
4. Lancez **ComptaPrivée AI** depuis un raccourci, sans terminal. Le programme
   ne doit pas demander de droits administrateur. Python, Git et le dépôt
   source ne sont pas des prérequis d'utilisation.

L'installateur et le programme sont **non signés**. Windows peut afficher un
avertissement ou bloquer leur lancement. Relevez le texte exact et l'étape ; ne désactivez aucune protection
pour poursuivre. Le nom d'éditeur « ComptaPrivée AI » est un libellé du produit,
pas une identité certifiée. La signature et l'identité finale restent à traiter.

## Documents, OCR et Office

Les PDF contenant du texte sont utilisables sans OCR. Pour les images ou PDF
scannés, Tesseract doit être installé séparément et accessible, avec les langues
`fra` et `eng` recommandées. L'application ne le télécharge pas automatiquement.
Son absence n'empêche pas le démarrage et doit produire un message explicite.

Word et Excel sont facultatifs pour lancer l'application. Les conversions
Office par COM exigent le produit correspondant installé sur Windows.
L'installateur de référence POST-V1-E3 intègre la correction Excel → PDF :
l'intitulé A1 et la valeur B2 ont été vérifiés dans un PDF produit par la GUI
installée avec Excel réel. Les colonnes sont ajustées pour l'export ; vérifiez
la mise en page des documents produits avant utilisation. Le classeur source
n'est pas modifié. La validation sur machine indépendante reste à effectuer.

Les valeurs extraites doivent être vérifiées et validées par une personne.
Les calculs portent sur 2025 ; les profils avancés restent bornés et certains
formulaires officiels sont préparés hors du logiciel. Les limites détaillées
figurent dans [la documentation fiscale](moteur_fiscal_2025.md).

## Données et sauvegarde

Les données locales se trouvent dans `%LOCALAPPDATA%\ComptaPriveeAI` : dossiers
fiscaux, base SQLite, paramètres, exports et journaux. Ce stockage n'est pas
chiffré. N'utilisez pas Program Files comme dossier de données ou de sauvegarde.

Dans **Paramètres → Sauvegarde**, créez une archive ZIP dans un emplacement de
votre choix. La sauvegarde actuelle contient la base, les paramètres, le profil
du cabinet et les dossiers fiscaux JSON. Elle ne remplace pas une copie séparée
des pièces originales, exports et autres fichiers : ne supposez pas qu'ils
sont inclus dans l'archive.

Si Windows refuse le remplacement du ZIP, l'ancienne archive est conservée.
L'application affiche un message et reste utilisable : réessayez après avoir
fermé les programmes utilisant ce fichier, ou choisissez un **nouveau nom**.
Ne considérez pas une opération refusée comme une sauvegarde réussie.

Pour restaurer, choisissez une archive créée par le logiciel et confirmez le
remplacement des données locales. Fermez puis relancez l'application après
restauration, comme le recommande le dialogue.

## Désinstaller et réinstaller

Fermez l'application puis utilisez la désinstallation Windows. Le programme
et ses raccourcis sont retirés ; `%LOCALAPPDATA%\ComptaPriveeAI` est **conservé**.
Une réinstallation permet de retrouver ces données. Sauvegardez-les avant
toute opération et ne supprimez pas ce dossier pour résoudre un problème.

Pour un signalement, fournissez l'étape, le message et le contexte Windows,
sans joindre de vraies données client. L'état des validations est détaillé dans
[le rapport POST-V1-E](validation_distribution_windows.md).
