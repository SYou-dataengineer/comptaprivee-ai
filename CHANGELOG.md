# Changelog

## 1.0.0 — validation finale, sans tag

- Moteur fiscal 2025 fédéral et Québec, estimations et traces, avec limites explicites
  dans le README et le référentiel fiscal.
- Extraction locale PDF/DOCX/images, OCR Tesseract et validation humaine des faits.
- Dossiers fiscaux JSON rétrocompatibles, identité stable et rapports PDF ;
  sauvegarde/restauration contrôlée avec validation et rollback.
- Travail autonome simple et cotisations dans le profil autonome pur publié ;
  location simple et DPA catégorie 1 bornée sans acquisitions/dispositions 2025.
- Pertes et reports documentés dans leurs profils bornés ; déclaration finale
  principale au décès limitée, sans succession complexe.
- Préparation interprovinciale et IMR avec suspension du calcul lorsque les
  formulaires externes sont requis ; inventaire et obligations des biens étrangers
  sans production automatique des formulaires.
- CI Linux complète et Windows ciblée avec GUI ; traitement local sans chiffrement
  applicatif ni transmission fiscale automatique.

Limites : 2025 uniquement, aucun T2203/TP-22 ou IMR complet, aucun profil emploi
et autonome combiné, résidence partielle hors calcul annuel, DPA complexe exclue.
Tesseract reste externe. Les sauvegardes n'incluent pas les pièces originales.
Voir [les limites connues](README.md#limites-connues-v10) et
[la checklist](docs/release_v1_checklist.md). Aucun tag n'est créé sans autorisation.

Validation FINAL-C2 : 227 tests ciblés Windows, puis une seule suite complète
locale de 7 501 tests réussis, 5 avertissements externes. Audit des fichiers suivis,
exclusions Git renforcées et cohérence des métadonnées contrôlés. Les CI du commit
publié constituent la dernière porte de publication, à vérifier dans le checkpoint.

## 1.0.0rc1 — préparation technique, non taguée

- Préparation comptable locale, validation humaine, dossiers fiscaux et estimations
  fédérales/Québec 2025 dans les périmètres décrits dans la documentation fiscale.
- FINAL-B1 : sauvegardes fiscales, restauration à destinations autorisées avec
  validation/rollback et identité UUID des dossiers.
- FINAL-B2 : refus des valeurs non finies, extraction T4 16A, typage JSON strict,
  résultats historiques non vérifiés et protection des champs textuels CSV.
- FINAL-C1 : README et installation Windows, checklist release, CI Windows ciblée,
  sélection fiscale fixée à 2025, métadonnées de préparation et correction de la
  dépréciation interne openpyxl.

Aucune transmission gouvernementale, aucun moteur 2026, aucun installateur final
et aucun tag v1.0 dans cette préparation. Voir les exclusions fiscales et les
validations restantes avant de décider de publier une release finale.
