# Matrice des données fiscales

Statut : **Inventaire initial**

| Donnée | Exemple source | Sensibilité | Stockage prévu | Journal autorisé ? |
|---|---|---:|---|---|
| Nom | T4 / RL-1 | Élevée | Local | Oui, avec prudence |
| Adresse | Dossier | Élevée | Local | Non par défaut |
| NAS | T4 / RL-1 | Très élevée | Local protégé | **Non** |
| Date naissance | Dossier client | Très élevée | Local protégé | Non |
| État civil | Dossier client | Très élevée | Local protégé | Non |
| Revenu emploi | T4 case 14 | Très élevée | Local | Contrôlé |
| Impôt retenu | T4 case 22 | Très élevée | Local | Contrôlé |
| REER | Reçu | Très élevée | Local | Contrôlé |
| Frais médicaux | Reçus | Très élevée | Local | Éviter détails médicaux |
| Coordonnées bancaires | Paiement/remboursement | Très élevée | Local protégé | **Non** |
| Signature | Autorisation | Très élevée | Local protégé | **Non** |
| Identifiants EFILE | Configuration | Critique | Coffre de secrets | **Jamais** |

## Règles

- NAS complet interdit dans les logs.
- Secrets interdits dans Git.
- Tests uniquement avec données fictives.
- Toute nouvelle catégorie de données doit être ajoutée à cette matrice avant développement.
