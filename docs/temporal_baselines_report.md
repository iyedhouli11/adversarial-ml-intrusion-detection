# Régression logistique et forêt sur le découpage par strate (Phase 4.3-b)

**Observé** = mesuré par `src/models/temporal_baselines.py`.
Données : lundi à mercredi uniquement, découpage par strate (jour x label) 60/20/20 avec intervalle de 1 %
(`src/data/temporal_split.py`). Entraînement : segment train (702 310 lignes). Évaluation : segment validation
(214 261 lignes, 15,00 % d'attaques). Le segment test, le jeudi et le vendredi n'ont pas été utilisés.
Hyperparamètres fixés à l'avance, sans réglage : stratégie `exclude`, graine 42, seuil 0,5, une seule exécution ;
forêt : `n_estimators=100`, `min_samples_leaf=5` ; régression logistique : `max_iter=500`.

## Observé

| Seuil 0,5 | Régression logistique | Random Forest |
|---|---|---|
| TN / FP | 181 647 / 470 | 182 110 / 7 |
| FN / TP | 250 / 31 894 | 9 / 32 135 |
| Précision | 0,9855 | 0,9998 |
| Rappel | 0,9922 | 0,9997 |
| F1 | 0,9888 | 0,9998 |
| PR-AUC (référence aléatoire 0,1500) | 0,9969 | 1,0000 (arrondi) |
| Entraînement / inférence | 7,7 s / 0,03 s | 35,8 s / 0,24 s |

- Taux de détection par famille (validation) : forêt >= 0,9949 pour toutes les familles ;
  régression logistique plus faible sur DoS Slowloris (0,8432) et DoS Slowhttptest (0,8850).
- Heartbleed : 2 flux en validation, aucune conclusion possible.
- `DoS Slowhttptest - Attempted` (étiqueté 0) : 24,75 % signalés par la régression logistique, 0 % par la forêt.
- Doublons exacts entre train et validation (variables du modèle) : 0,0748 au total ;
  0,0000 pour les attaques, 0,0880 pour les flux normaux.

## Interprétation (hypothèses, non démontrées)
- Les mêmes modèles obtiennent une PR-AUC de 0,41 à 0,61 sur le jeudi et d'environ 1 ici : cohérent avec
  l'hypothèse d'un échec du jeudi dû à une famille absente de l'entraînement, mais ce découpage ne
  teste pas cette hypothèse isolément.
- Un score de 1,0 est une borne optimiste, pas une performance de déploiement.

## Limites
- Flux d'une même campagne similaires malgré l'intervalle de 1 % ; doublons proches non mesurés.
- 8,8 % des flux normaux de validation ont un jumeau exact dans le train.
- Le choix du protocole a été fait après les résultats du jeudi (validation) ; le jeudi est donc utilisé
  pour le développement et non plus comme évaluation indépendante.
- Une seule graine, aucun réglage, aucune comparaison statistique entre les deux modèles.

## Planifié
- XGBoost sur ce découpage, même protocole.
- Sensibilité aux doublons (retirer les lignes de validation dupliquées du train) et à la taille de l'intervalle.