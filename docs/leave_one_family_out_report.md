# Une famille retirée de l'entraînement (Phase 4.5-b)

**Observé** = mesuré par `src/models/leave_one_family_out.py`.
Données : lundi à mercredi, découpage par strate (intervalle 1 %). Pour chaque famille F, F et « F - Attempted »
sont retirées du segment train ; prétraitement et modèle sont ajustés sans elles. Évaluation : flux de validation
de F contre flux BENIGN de validation, seuil 0,5. Le segment test, le jeudi et le vendredi n'ont pas été utilisés.
Hyperparamètres fixés à l'avance, graine 42, une seule exécution. Heartbleed est exclu (7 flux en train).

## Observé

| Famille retirée | Flux F (validation) | Modèle | Rappel de F | BENIGN signalés | PR-AUC | Référence aléatoire |
|---|---|---|---|---|---|---|
| DoS Hulk | 28 524 | LogReg | 0,5728 | 0,0007 | 0,9356 | 0,1361 |
| DoS Hulk | 28 524 | RandomForest | 0,0198 | 0,0000 | 0,9988 | 0,1361 |
| DoS Hulk | 28 524 | XGBoost | 0,3517 | 0,0000 | 0,9928 | 0,1361 |
| DoS GoldenEye | 1 362 | LogReg | 0,8700 | 0,0013 | 0,8662 | 0,0075 |
| DoS GoldenEye | 1 362 | RandomForest | 0,5932 | 0,0000 | 0,9253 | 0,0075 |
| DoS GoldenEye | 1 362 | XGBoost | 0,7203 | 0,0000 | 0,9840 | 0,0075 |
| DoS Slowhttptest | 313 | LogReg | 0,7987 | 0,0015 | 0,5346 | 0,0017 |
| DoS Slowhttptest | 313 | RandomForest | 0,8594 | 0,0000 | 0,9946 | 0,0017 |
| DoS Slowhttptest | 313 | XGBoost | 0,8594 | 0,0000 | 0,9979 | 0,0017 |
| DoS Slowloris | 695 | LogReg | 0,4763 | 0,0018 | 0,4699 | 0,0038 |
| DoS Slowloris | 695 | RandomForest | 0,4763 | 0,0000 | 0,9206 | 0,0038 |
| DoS Slowloris | 695 | XGBoost | 0,4763 | 0,0000 | 0,9791 | 0,0038 |
| FTP-Patator | 715 | LogReg | 0,0000 | 0,0018 | 0,0094 | 0,0039 |
| FTP-Patator | 715 | RandomForest | 0,0000 | 0,0000 | 0,4659 | 0,0039 |
| FTP-Patator | 715 | XGBoost | 0,0000 | 0,0000 | 0,0632 | 0,0039 |
| SSH-Patator | 533 | LogReg | 0,0000 | 0,0011 | 0,0062 | 0,0029 |
| SSH-Patator | 533 | RandomForest | 0,0000 | 0,0001 | 0,0230 | 0,0029 |
| SSH-Patator | 533 | XGBoost | 0,0000 | 0,0001 | 0,0162 | 0,0029 |

- Les deux familles Patator ne sont détectées par aucun modèle à 0,5, bien que l'autre Patator reste dans l'entraînement.
- Les familles DoS sont partiellement détectées (rappel de 0,02 à 0,87 selon famille et modèle).
- Rappel de Slowloris identique pour les trois modèles (0,4763, soit environ 331 flux sur 695) et celui de
  Slowhttptest identique pour RF et XGBoost (0,8594, environ 269 sur 313) : mêmes flux détectés ou ratés. Non expliqué.
- Pour Hulk, la forêt a un rappel de 0,0198 à 0,5 mais une PR-AUC de 0,9988 : les scores classent bien
  les flux Hulk mais restent sous le seuil. Aucun seuil n'est retenu.

## Interprétation (hypothèses, non démontrées)
- La généralisation à une famille non vue dépend fortement de la famille : nulle pour les Patator, partielle pour les DoS.
- Cohérent avec l'échec sur le jeudi (portscan très différent de l'entraînement), sans le démontrer.
- Un attaquant qui change de famille obtient une « évasion sans effort » : référence pour le modèle de menace.

## Limites
- Une seule graine ; petites familles (313 à 715 flux) ; aucun test statistique.
- Seuls les flux de F et le BENIGN sont évalués ; les autres attaques sont exclues de l'évaluation.
- Le rappel à 0,5 dépend du seuil et de la calibration de chaque modèle ; la PR-AUC mesure le classement.
- Les familles proches (autres DoS, l'autre Patator) restent dans l'entraînement.

## Planifié
- Réglage d'hyperparamètres sur la validation avec une grille déclarée à l'avance (voir ci-dessous).
- Phase 5 : modèle de menace finalisé et contrôlabilité des variables, avant l'attaque.