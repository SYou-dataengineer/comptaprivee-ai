# EFVP — Agent fiscal ComptaPrivée AI

Statut : **Brouillon évolutif — Phase 0**

Une évaluation des facteurs relatifs à la vie privée doit accompagner le développement du futur Agent fiscal et être mise à jour lorsque l’architecture, les données ou les communications changent.

## 1. Description du projet

L’Agent fiscal vise à permettre à un comptable de créer un dossier fiscal, importer des documents, les reconnaître et les classer, extraire les données utiles, appliquer un moteur fiscal déterministe, signaler les incohérences, puis préparer le dossier pour révision humaine.

## 2. Portée initiale

- particuliers;
- Québec + fédéral;
- T4, RL-1 et pièces justificatives courantes;
- préparation locale uniquement.

Hors portée initiale : transmission ARC, transmission Revenu Québec, décisions entièrement automatisées, hébergement cloud et sociétés.

## 3. Renseignements personnels prévus

Identité, coordonnées, NAS, date de naissance, état civil, revenus, retenues, prestations, frais médicaux, frais de garde, études, dons, REER, renseignements sur conjoint/personnes à charge, pièces justificatives et données fiscales calculées.

Niveau de sensibilité global : **Très élevé**.

## 4. Flux des données

1. Import local.
2. Lecture locale.
3. OCR/extraction locale.
4. Classification locale.
5. Validation des données.
6. Calcul fiscal local.
7. Révision du comptable.
8. Production locale.
9. Transmission externe : **interdite dans la Phase 0**.

## 5. Risques principaux

| Risque | Gravité | Mesure prévue |
|---|---|---|
| Accès non autorisé | Élevée | contrôle d’accès + chiffrement à prévoir |
| Fuite de NAS | Très élevée | masquage interface et journaux |
| Mauvaise extraction OCR | Élevée | validation humaine + score de confiance |
| Mauvais calcul fiscal | Très élevée | moteur déterministe versionné + tests |
| Transmission accidentelle | Très élevée | fonctions réseau désactivées par défaut |
| Conservation excessive | Élevée | politique de conservation |
| Données sensibles dans les logs | Élevée | minimisation des journaux |
| Utilisation d’une IA externe | Très élevée | interdite par défaut |

## 6. Mesures minimales avant données réelles

- aucune donnée fiscale dans Git;
- aucun NAS complet dans les logs;
- aucun secret EFILE dans le dépôt;
- données de démonstration fictives;
- journal d’audit local;
- validation humaine avant finalisation;
- sauvegardes protégées;
- suppression contrôlée;
- fonctions réseau désactivées par défaut.

## 7. Décisions de conception

- OCR/IA ne détermine pas l’impôt final.
- Les règles fiscales sont séparées par année et juridiction.
- Chaque valeur calculée garde une référence vers sa source.
- Une donnée incertaine est marquée `À VÉRIFIER`.
- Une déclaration ne peut être `PRÊTE À TRANSMETTRE` sans validation humaine.
- Les transmissions restent inactives avant certification.

## 8. Communications hors Québec

Avant toute communication ou conservation de renseignements personnels à l’extérieur du Québec : réaliser l’EFVP appropriée, documenter le fondement juridique et les mesures de protection, puis établir les ententes nécessaires.

## 9. Approbations à compléter

- Responsable protection RP : `[À désigner]`
- Responsable sécurité : `[À désigner]`
- Responsable fiscal : `[À désigner]`
- Validation juridique : `[À obtenir]`

## Sources officielles

- https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/responsable-protection-renseignements-personnels-entreprise
- https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25
