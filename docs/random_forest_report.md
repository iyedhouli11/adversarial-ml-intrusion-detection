# Random Forest (Phase 4.3)

**Observé** = mesuré par `src/models/random_forest_baseline.py`.
Entraînement : lundi à mercredi. Évaluation : jeudi (validation). Le vendredi n'a pas été chargé.
Paramètres fixés à l'avance, sans réglage : `n_estimators=100`, `min_samples_leaf=5`, graine 42,
stratégie de header `exclude`, pas de scaling. Une seule exécution.

## Observé

- PR-AUC : 0,4156 (référence aléatoire 0,1986 ; régression logistique B : 0,6091).
- Temps : entraînement 75,5 s, inférence sur jeudi 0,45 s (régression logistique B : 27,2 s et 0,12 s).

| Seuil | TN | FP | FN | TP | Précision | Rappel | F1 | Alertes / 10 000 | Rappel portscan | BENIGN signalés |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,5 | 290 166 | 3 | 71 907 | 0 | 0,0000 | 0,0000 | 0,0000 | 0 | 0,0000 | 0,0000 |
| 0,3 | 290 161 | 8 | 71 904 | 3 | 0,2727 | 0,0000 | 0,0001 | 0 | 0,0000 | 0,0000 |
| 0,1 | 290 087 | 82 | 71 545 | 362 | 0,8153 | 0,0050 | 0,0100 | 12 | 0,0047 | 0,0003 |
| 0,05 | 289 924 | 245 | 71 206 | 701 | 0,7410 | 0,0097 | 0,0192 | 26 | 0,0093 | 0,0007 |
| 0,01 | 288 883 | 1 286 | 54 338 | 17 569 | 0,9318 | 0,2443 | 0,3871 | 521 | 0,2439 | 0,0039 |

- À 0,5, aucune attaque de jeudi n'est détectée, famille par famille.
- Aucun seuil n'est retenu.
- Importances (impurity-based) dominées par des variables de longueur de paquet, corrélées entre elles :
  Bwd Packet Length Std, Packet Length Std, Bwd Packet Length Mean, Bwd Segment Size Avg, Packet Length Variance.

## Interprétation (hypothèse, non testée)
- L'hypothèse « le modèle linéaire est trop faible » n'est pas confirmée : la forêt a une PR-AUC plus basse.
- Hypothèse en cours : le portscan est absent de l'entraînement, et le décalage de famille explique
  l'échec des deux modèles supervisés. À tester avec un diagnostic « dans la distribution ».

## Limites
- Une seule graine, aucun réglage d'hyperparamètres.
- Les probabilités de la forêt et de la régression logistique ne sont pas calibrées de la même façon :
  comparer à seuil égal n'est pas équitable ; la PR-AUC est le comparatif sans seuil.
- Jeudi est dominé par le portscan (99,8 % des attaques) ; les familles web ont 13 à 73 flux.
- Les importances de variables corrélées ne sont pas des effets isolés.
- Avec ce découpage, aucun détecteur n'est exploitable pour l'attaque d'évasion.

## Planifié
- Diagnostic dans la distribution (train seulement, découpage chronologique dans chaque jour).
- Décision sur le protocole, puis XGBoost (4.4).