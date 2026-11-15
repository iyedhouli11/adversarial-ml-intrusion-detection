# XGBoost sur le découpage par strate (Phase 4.4)

**Observé** = mesuré par `src/models/xgboost_temporal.py`.
Données : lundi à mercredi, découpage par strate (jour x label) 60/20/20 avec intervalle de 1 %.
Entraînement : segment train (702 310 lignes). Évaluation : segment validation (214 261 lignes, 15,00 % d'attaques).
Le segment test, le jeudi et le vendredi n'ont pas été utilisés.
Hyperparamètres fixés à l'avance, sans réglage : `n_estimators=200`, `max_depth=6`, `learning_rate=0.1`,
`tree_method=hist`, graine 42, stratégie `exclude`, seuil 0,5, une seule exécution.

## Observé

| Seuil 0,5 | Régression logistique | Random Forest | XGBoost |
|---|---|---|---|
| TN / FP | 181 647 / 470 | 182 110 / 7 | 182 058 / 59 |
| FN / TP | 250 / 31 894 | 9 / 32 135 | 0 / 32 144 |
| Précision | 0,9855 | 0,9998 | 0,9982 |
| Rappel | 0,9922 | 0,9997 | 1,0000 |
| F1 | 0,9888 | 0,9998 | 0,9991 |
| PR-AUC (référence aléatoire 0,1500) | 0,9969 | 1,0000 (arrondi) | 1,0000 (arrondi) |
| Entraînement / inférence | 7,7 s / 0,03 s | 35,8 s / 0,24 s | 9,4 s / 0,08 s |

- XGBoost : toutes les familles d'attaque détectées à 1,0000 (Heartbleed : 2 flux seulement).
- `DoS Slowhttptest - Attempted` (étiqueté 0) : 9,57 % signalés par XGBoost (environ 58 flux sur 606), ce qui
  explique presque tous ses 59 faux positifs ; 0 % pour la forêt, 24,75 % pour la régression logistique.
- Importances (gain) : `Bwd Packet Length Std` 0,6068 ; `Packet Length Mean` 0,0629 ; `Bwd IAT Max` 0,0560 ;
  `Down/Up Ratio` 0,0431 ; `Fwd IAT Max` 0,0354. La forêt avait aussi `Bwd Packet Length Std` en première position.

## Interprétation (hypothèses, non démontrées)
- Les trois modèles sont au plafond de cette validation : elle ne permet plus de les départager.
- Les écarts RF / XGBoost portent surtout sur des flux « Attempted » ambigus, dépendants de la définition de la cible.
- Une forte dépendance à `Bwd Packet Length Std` peut constituer une surface d'attaque pour l'évasion ;
  à confronter à la contrôlabilité des variables.

## Limites
- Borne optimiste : flux d'une même campagne similaires malgré l'intervalle ; 8,8 % des flux normaux de validation
  dupliqués exactement dans le train.
- Une seule graine, aucun réglage d'hyperparamètres, aucune comparaison statistique entre modèles.
- Le protocole a été choisi après les résultats du jeudi (validation).
- Importances de variables corrélées : pas des effets isolés.

## Planifié
- Phase 4.5 : sensibilité à l'intervalle et aux doublons, plusieurs graines, réglage sur la validation,
  XGBoost sur le protocole par jour (jeudi) pour compléter l'étude du décalage.