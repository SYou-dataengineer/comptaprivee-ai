# Contrat de préparation multi-années

Statut FINAL-C1 : documentation et verrouillage de la sélection actuelle seulement.
Aucun moteur 2026 n'est implémenté.

## État audité

Les moteurs et constantes sont répartis dans `tax_*_2025.py`. Les orchestrateurs
`tax_estimation_2025`, `tax_calculation_trace_2025` et `tax_report_pdf_2025` portent
explicitement le millésime. La GUI importe ces profils et libelle les commandes
2025 ; `tax_case_storage` importe également leurs types pour la persistance.
Ces couplages doivent être traités lors de l'ajout d'un moteur, pas par renommage
massif ni par substitution de constantes globales.

`tax_case.annee_fiscale_par_defaut` et `annees_fiscales_disponibles` ne consultent
plus l'horloge : la seule année proposée est 2025. Les arguments historiques restent
acceptés pour compatibilité mais ne permettent pas de sélectionner un autre barème.
Les refus existants des moteurs pour une année différente de 2025 restent en place.

Le JSON conserve `annee_fiscale` (entier strict), `schema_version` et le `case_id`
indépendant du nom. Les anciens résumés restent non vérifiés. Un changement de
moteur doit entraîner un recalcul, jamais la réutilisation d'un résumé/PDF historique.

## Interface future proposée, non implémentée

```python
tax_year = 2025
engine = get_tax_engine(tax_year)  # registre explicite de moteurs validés
result = engine.estimate(facts)
```

Le registre futur devra refuser explicitement toute année non livrée. Aucun fallback
vers 2025, ni sélection par `date.today()`, ni partage mutable de constantes.
`get_tax_engine(2026)` restera interdit tant que le moteur 2026 n'est pas publié.

## Conditions d'ajout de 2026

1. Sources et paramètres officiels 2026, tests et périmètre séparés.
2. Adaptateurs de profils/JSON explicites, avec migrations versionnées et sauvegarde
   préalable ; ne pas réinterpréter les faits historiques sous un autre millésime.
3. Année obligatoire propagée du dossier aux calculs, traces, PDF et exports.
4. Identification du moteur/version dans les résultats futurs ; historique invalidé
   si cette provenance ne permet pas de vérifier la concordance.
5. Tests de refus d'années non supportées et isolation des constantes entre années.
6. Préservation du fonctionnement 2025 pour les dossiers tardifs/corrections.

Le chemin par UUID ne sélectionne pas de moteur. Les filtres de listes, rapports
et écrans devront utiliser l'année du dossier, indépendamment de l'année du poste.
