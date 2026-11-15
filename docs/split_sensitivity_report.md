# Sensibilité du découpage par strate (Phase 4.5-a)

**Observé** = mesuré par `src/models/split_sensitivity.py`.
Données : lundi à mercredi. Modèles ajustés sur le segment train, évalués sur le segment validation, seuil 0,5.
Le segment test, le jeudi et le vendredi n'ont pas été utilisés. Hyperparamètres inchangés (fixés à l'avance),
graine 42, une seule exécution par configuration.

Configurations : intervalle de 1 % ou 5 % autour des coupures, avec ou sans suppression des doublons exacts
(sur les variables du modèle, stratégie `exclude`) **avant** le découpage ; on garde la ligne la plus ancienne.

## Observé

- La config 1 (1 %, sans déduplication) reproduit exactement les résultats précédents.
- Déduplication : 82 453 lignes retirées (6,9 % des 1 190 343). La part d'attaques passe de 0,1500 à 0,1612 :
  les lignes retirées sont presque toutes normales (déduction).

| Config | Modèle | PR-AUC | Précision | Rappel | F1 | FP | FN | Rappel min. par famille |
|---|---|---|---|---|---|---|---|---|
| gap 1 % | LogReg | 0,9969 | 0,9855 | 0,9922 | 0,9888 | 470 | 250 | 0,8432 |
| gap 1 % | RandomForest | 1,0000 | 0,9998 | 0,9997 | 0,9998 | 7 | 9 | 0,9949 |
| gap 1 % | XGBoost | 1,0000 | 0,9982 | 1,0000 | 0,9991 | 59 | 0 | 1,0000 |
| gap 5 % | LogReg | 0,9967 | 0,9812 | 0,9920 | 0,9866 | 339 | 143 | 0,7902 |
| gap 5 % | RandomForest | 1,0000 | 0,9997 | 0,9996 | 0,9996 | 5 | 8 | 0,9908 |
| gap 5 % | XGBoost | 1,0000 | 0,9967 | 0,9999 | 0,9983 | 60 | 1 | 0,9987 |
| gap 1 % + dedup | LogReg | 0,9966 | 0,9854 | 0,9923 | 0,9888 | 471 | 249 | 0,8489 |
| gap 1 % + dedup | RandomForest | 1,0000 | 0,9997 | 0,9997 | 0,9997 | 9 | 10 | 0,9941 |
| gap 1 % + dedup | XGBoost | 1,0000 | 0,9981 | 1,0000 | 0,9991 | 60 | 0 | 1,0000 |
| gap 5 % + dedup | LogReg | 0,9967 | 0,9809 | 0,9919 | 0,9864 | 345 | 144 | 0,7902 |
| gap 5 % + dedup | RandomForest | 1,0000 | 0,9998 | 0,9997 | 0,9997 | 4 | 5 | 0,9947 |
| gap 5 % + dedup | XGBoost | 1,0000 | 0,9968 | 1,0000 | 0,9984 | 58 | 0 | 1,0000 |

(Rappel min. par famille : parmi les familles d'attaque d'au moins 100 flux en validation.)

## Interprétation (hypothèses, non démontrées)
- Les doublons exacts et la taille de l'intervalle n'expliquent pas les scores proches de 1 : les écarts de F1
  restent inférieurs ou égaux à 0,0024, sur une seule graine et sur des lignes de validation différentes.
- Restent ouvertes : la similarité entre flux voisins d'une même campagne (non mesurée), et la séparabilité
  intrinsèque des familles DoS et Patator avec ces variables.

## Limites
- Les lignes de validation diffèrent d'une configuration à l'autre : FP et FN ne sont pas directement comparables.
- Une seule graine ; aucun test statistique.
- Les temps d'entraînement sont trop variables (forêt : 34,9 s à 65,2 s à taille comparable) pour être comparés.

## Planifié
- Test « une famille retirée de l'entraînement » (validation uniquement), pour mesurer la généralisation à une famille non vue.
- Plusieurs graines ; réglage sur la validation ; XGBoost sur le protocole par jour (jeudi).