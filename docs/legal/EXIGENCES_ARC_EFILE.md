# ARC — Exigences EFILE à intégrer

Statut : **Transmission désactivée**

ComptaPrivée AI peut préparer des données et calculs avant certification, mais ne doit pas transmettre des T1 de clients par EFILE tant que les exigences du programme ne sont pas satisfaites.

## Conditions principales à prévoir

- logiciel compatible/certifié EFILE;
- accès EFILE approuvé pour le préparateur;
- renouvellement annuel lorsque requis;
- formulaire T183 complété avant transmission;
- validation des exclusions EFILE;
- traitement des accusés d’acceptation/rejet;
- sécurité des identifiants;
- aucun identifiant EFILE dans Git;
- journalisation sans exposer de données sensibles.

## Règle projet

`TRANSMISSION_ARC = False`

Cette valeur restera `False` jusqu’à ce que la certification et les contrôles requis soient en place.

## Sources officielles

- https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-individuals/efile-electronic-filers.html
- https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-individuals/efile-electronic-filers/efile-certified-software-efile-program.html
- https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-individuals/efile-electronic-filers/forms-t183-t1013.html
