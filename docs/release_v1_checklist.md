# Checklist de release technique v1.0

Version de préparation : **1.0.0rc1**, sans tag. Cette checklist doit être revue
sur le commit exact candidat à la release finale. La réussite de FINAL-C1 ne
constitue pas une autorisation de taguer ni de commercialiser le produit.

## Contrôles acquis

- [x] P0 ouverts parmi ceux audités en FINAL-A : 0 après FINAL-B1.
- [x] P1 ouverts parmi ceux audités en FINAL-A : 0 après FINAL-B2.
- [x] README utilisateur actualisé et procédure Windows documentée.
- [x] Paramètres 2025 exclusivement ; refus moteur de 2026 et sélection indépendante
  de l'horloge testés. Aucun moteur 2026 implémenté.
- [x] Version de préparation définie dans `pyproject.toml` ; changelog prêt.
- [x] Installation dans un venv Windows neuf : requirements, pip check, imports,
  lancement de la CLI et initialisation Tk vérifiés.
- [x] Chemins avec espaces/Unicode, JSON, CSV et round-trip sauvegarde/restauration
  couverts par les tests Windows ciblés.
- [x] Confidentialité locale et absence de chiffrement applicatif documentées.
- [x] Aucun PDF/DOCX/CSV/XLSX/JSON/DB de données suivi détecté lors du contrôle Git ;
  recherche de secrets usuels sans correspondance dans source/tests/docs.
- [x] Code fiscal 2025 inchangé ; correction interne openpyxl testée.
- [x] CI Linux complète conservée ; job Windows ciblé ajouté avec Tk réel.

## Portes de publication à vérifier sur le commit candidat

- [x] Suite complete locale FINAL-C1 : **7 501 passed, 5 warnings**, Python 3.12.10 Windows.
- [ ] CI Linux verte sur le commit publié.
- [ ] CI Windows verte sur le même commit (persistance, chemins, JSON, CSV, GUI).
- [ ] `git status --short` vide et `git diff --check` sans erreur après publication.
- [ ] Vérifier une dernière fois les fichiers du commit : aucune donnée client,
  pièce sensible, sauvegarde, secret ou fichier temporaire.
- [ ] Autorisation humaine explicite avant création du tag v1.0.

Les quatre premières preuves finales sont à relever dans le checkpoint de session
et les exécutions GitHub Actions du commit. Ne pas réutiliser une CI d'un ancien
commit pour approuver un nouveau candidat.

## Limites et vérifications manuelles restantes

- Windows CI est ciblée et n'installe pas Tesseract ; OCR couvert en Linux CI et
  localement sous Windows. Tester le parcours complet sur une machine Windows
  vierge avec l'installateur OCR retenu avant distribution finale.
- Vérifier manuellement les écrans/DPI usuels et un dossier fictif de bout en bout
  (import, validation, estimation, PDF, sauvegarde, fermeture, restauration).
- Conserver la liste de versions/binaire OCR et étudier le verrouillage des
  dépendances transitives pour une installation entièrement reproductible hors ligne.
- Suivre les cinq avertissements SWIG/PyMuPDF et les annonces des runners/actions.
- Les documents de conformité commerciale restent à valider ; aucune licence,
  authentification ou paiement n'est ajouté.
- La dette des grands modules et le futur registre de moteurs annuels restent
  documentés, sans refactor dans FINAL-C1.

## Interdictions de cette session

- [x] Aucun tag v1.0 créé.
- [x] Aucun exécutable/installateur final créé.
- [x] Aucun moteur fiscal 2026 commencé.
