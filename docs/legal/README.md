# Phase 0 — Conformité de l’Agent fiscal

Statut : **Brouillon de travail — à valider avant mise en production**

Cette section documente les mesures de conformité prévues pour le futur module **Agent fiscal** de ComptaPrivée AI.

## Principes obligatoires

1. **Local par défaut** : aucune donnée fiscale n’est transmise sur Internet automatiquement.
2. **Minimisation** : ne recueillir que les renseignements nécessaires au dossier fiscal.
3. **Validation humaine obligatoire** : l’agent prépare et calcule, le comptable valide.
4. **Traçabilité** : chaque montant calculé doit pouvoir être relié à sa source documentaire.
5. **Transmission gouvernementale désactivée tant que non certifiée**.
6. **Séparation des responsabilités** : IA/OCR pour la lecture; moteur fiscal déterministe pour le calcul; comptable pour la validation; services certifiés pour la transmission.
7. **Protection par défaut** : les paramètres les plus protecteurs doivent être activés sans action de l’utilisateur.

## Documents de conformité

- `EFVP_AGENT_FISCAL.md`
- `POLITIQUE_CONFIDENTIALITE.md`
- `POLITIQUE_CONSERVATION_DONNEES.md`
- `PROCEDURE_INCIDENT_CONFIDENTIALITE.md`
- `MATRICE_DONNEES_FISCALES.md`
- `EXIGENCES_ARC_EFILE.md`
- `EXIGENCES_REVENU_QUEBEC.md`

## Statut des transmissions

- ARC / EFILE : **DÉSACTIVÉ**
- Revenu Québec : **DÉSACTIVÉ**
- Import automatique de données gouvernementales : **DÉSACTIVÉ**
- Envoi vers une IA externe : **DÉSACTIVÉ**

## Avertissement

Ces documents constituent un cadre de conception et de conformité interne. Ils ne remplacent pas un avis juridique, fiscal ou de cybersécurité professionnel.

## Sources officielles principales

- Commission d’accès à l’information du Québec : https://www.cai.gouv.qc.ca/
- ARC — EFILE : https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-individuals/efile-electronic-filers.html
- Revenu Québec — Concepteurs de produits : https://www.revenuquebec.ca/fr/partenaires/concepteurs-de-produits/
