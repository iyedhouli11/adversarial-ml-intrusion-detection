# Réglage des hyperparamètres sur la validation (Phase 4.5-c)

**Observé** = mesuré par `src/models/tune_on_validation.py`.
Données : lundi à mercredi, découpage par strate (intervalle 1 %). Chaque modèle est ajusté sur le segment train
et évalué sur le segment validation. Le segment test, le jeudi et le vendredi n'ont pas été utilisés.
La grille et la règle ont été déclarées dans le code **avant** l'exécution : meilleure PR-AUC ; les configurations
à moins de 0,001 de la meilleure sont considérées ex æquo et on garde la plus simple.
Seuil 0,5, graine 42, une seule exécution (relancée une fois : résultats identiques ; temps non reproductibles).

## Observé

| Modèle | Paramètres | PR-AUC | F1 | FP | FN |
|---|---|---|---|---|---|
| LogReg | C=0,01 | 0,995645 | 0,980035 | 476 | 801 |
| LogReg | C=0,1 | 0,996517 | 0,987865 | 509 | 274 |
| LogReg | C=1 | 0,996854 | 0,988839 | 470 | 250 |
| LogReg | C=10 | 0,996711 | 0,988816 | 495 | 227 |
| RandomForest | 100 arbres, feuille 1 | 1,000000 | 0,999876 | 5 | 3 |
| RandomForest | 100 arbres, feuille 5 | 1,000000 | 0,999751 | 7 | 9 |
| RandomForest | 100 arbres, feuille 20 | 0,999998 | 0,999206 | 11 | 40 |
| RandomForest | 300 arbres, feuille 1 | 1,000000 | 0,999876 | 5 | 3 |
| RandomForest | 300 arbres, feuille 5 | 1,000000 | 0,999751 | 7 | 9 |
| RandomForest | 300 arbres, feuille 20 | 0,999998 | 0,999222 | 12 | 38 |
| XGBoost | profondeur 3, 100 arbres | 0,999997 | 0,999331 | 7 | 36 |
| XGBoost | profondeur 3, 200 arbres | 0,999999 | 0,999829 | 9 | 2 |
| XGBoost | profondeur 6, 100 arbres | 0,999999 | 0,999052 | 60 | 1 |
| XGBoost | profondeur 6, 200 arbres | 1,000000 | 0,999083 | 59 | 0 |
| XGBoost | profondeur 9, 100 arbres | 1,000000 | 0,999938 | 4 | 0 |
| XGBoost | profondeur 9, 200 arbres | 1,000000 | 0,999938 | 4 | 0 |

## Sélection par la règle déclarée (résultat principal)

| Modèle | Ex æquo | Configuration retenue | PR-AUC | FP / FN |
|---|---|---|---|---|
| LogReg | 3 | C=0,1 | 0,996517 | 509 / 274 |
| RandomForest | 6 | 100 arbres, feuille 20 | 0,999998 | 11 / 40 |
| XGBoost | 6 | profondeur 3, 100 arbres | 0,999997 | 7 / 36 |

## Lecture secondaire (choisie après avoir vu les résultats)
À PR-AUC équivalente, des configurations donnent moins de faux négatifs : forêt à feuille 1 (5 FP / 3 FN),
XGBoost de profondeur 9 (4 FP / 0 FN). Ce critère n'était pas déclaré à l'avance.

## Interprétation (hypothèses, non démontrées)
- La PR-AUC est saturée pour la forêt et XGBoost : l'écart total est inférieur à 0,000003, bien en dessous de la
  tolérance de 0,001. La règle départage donc par simplicité, pas par performance.
- Cette tolérance est un choix de conception qui n'avait pas anticipé cette saturation.

## Limites
- Validation quasi saturée, une seule graine, aucun test statistique.
- La validation par strate a déjà servi à choisir le protocole : ce n'est plus un jeu indépendant.
- Les temps d'entraînement varient d'une exécution à l'autre (charge de la machine) et ne sont pas rapportés.
- Le seuil 0,5 est fixé ; aucun seuil n'est retenu.

## Planifié
- Phase 5 : modèle de menace et contrôlabilité des variables, avant l'attaque.
- Évaluation finale unique sur le segment test (et le vendredi), après gel de toutes les décisions.