# Attaque d'évasion contre les trois détecteurs retenus (Phase 5, extension décidée après l'attaque initiale)

**Observé** = mesuré par `src/attacks/multi_target_attack.py`.
Même code d'attaque que `random_search_attack.py` (spécification v1) appliqué aux trois configurations retenues par la règle déclarée du réglage :
régression logistique (C = 0,1), forêt (100 arbres, `min_samples_leaf` 20) et XGBoost (profondeur 3, 100 arbres). Chaque détecteur est ajusté sur le segment train
et attaqué sur ses propres flux de validation détectés à 0,5 (au plus 300 par famille, graine 42) : les populations diffèrent d'un détecteur à l'autre.
Segment test, jeudi et vendredi non chargés. Une seule exécution. Cette extension a été décidée après avoir vu les résultats de l'attaque contre XGBoost : elle est post hoc.

## Contrôles
- Les lignes XGBoost reproduisent exactement l'attaque initiale (2/300 pour Slowhttptest à A = 1 et A = 2, 0 ailleurs ; médianes de requêtes 43 et 2).
- Identité s = t = 1 : écart maximal de score 9,99e-16 (régression logistique), 2,22e-16 (forêt), 0 (XGBoost) ; 0 bascule sous 0,5.

## Observé : performance propre (validation, seuil 0,5)
Régression logistique : rappel 0,9915, 509 faux positifs. Forêt : rappel 0,9988, 11 faux positifs. XGBoost : rappel 0,9989, 7 faux positifs.
Flux attaqués : régression logistique 1 777 (GoldenEye 300, Hulk 300, Slowhttptest 275, Slowloris 300, FTP-Patator 300, Heartbleed 2, SSH-Patator 300) ; forêt et XGBoost 1 800 (Heartbleed exclu : 0 détecté).
Rappel de validation avant attaque par famille : régression logistique GoldenEye 0,9545, Hulk 0,9987, Slowhttptest 0,8786, Slowloris 0,8302, FTP-Patator 1,0000, SSH-Patator 0,9625 ;
forêt 0,9750 / 0,9999 / 0,9936 / 1,0000 / 1,0000 / 1,0000 ; XGBoost 0,9816 / 0,9998 / 0,9936 / 1,0000 / 1,0000 / 1,0000.

## Observé : taux d'évasion par amplitude A (0,1 / 0,25 / 0,5 / 1 / 2)

| Détecteur | Famille | 0,1 | 0,25 | 0,5 | 1 | 2 |
|---|---|---|---|---|---|---|
| LogReg | DoS GoldenEye | 0,0100 | 0,0233 | 0,0533 | 0,1367 | 0,2667 |
| LogReg | DoS Hulk | 0,0000 | 0,0033 | 0,0067 | 0,0500 | 0,2300 |
| LogReg | DoS Slowhttptest (275 flux) | 0,0145 | 0,0909 | 0,0909 | 0,0909 | 0,2400 |
| LogReg | DoS Slowloris | 0,0000 | 0,0033 | 0,0100 | 0,0100 | 0,0767 |
| LogReg | FTP-Patator | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| LogReg | Heartbleed (2 flux) | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,5000 |
| LogReg | SSH-Patator | 0,1167 | 0,8300 | 1,0000 | 1,0000 | 1,0000 |
| Forêt | DoS GoldenEye | 0,0000 | 0,0000 | 0,0000 | 0,0033 | 0,0033 |
| Forêt | DoS Hulk | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| Forêt | DoS Slowhttptest | 0,0000 | 0,0000 | 0,0000 | 0,0033 | 0,0100 |
| Forêt | DoS Slowloris | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| Forêt | FTP-Patator | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| Forêt | SSH-Patator | 0,0000 | 0,0000 | 0,0000 | 0,4967 | 1,0000 |
| XGBoost | DoS Slowhttptest | 0,0000 | 0,0000 | 0,0000 | 0,0067 | 0,0067 |
| XGBoost | autres familles | 0 | 0 | 0 | 0 | 0 |

Intervalle de Wilson à 95 % : borne haute 0,0126 pour 0/300 ; 0,0240 pour 2/300. Médiane de requêtes des flux évadés : 1 à 78 (régression logistique), 3 à 23 (forêt), 43 puis 2 (XGBoost).
Score minimal médian atteint à A = 2 (score initial médian entre parenthèses) :
régression logistique GoldenEye 1,0000 (1,0000), Hulk 0,9552 (0,9998), Slowhttptest 0,5635 (0,9999), Slowloris 0,8097 (1,0000), FTP-Patator 0,7003 (0,8548), SSH-Patator 0,0037 (0,6784) ;
forêt GoldenEye 0,8691, Hulk 0,8907, Slowhttptest 0,9001, Slowloris 0,9262, FTP-Patator 0,6543, SSH-Patator 0,4573 ; XGBoost 0,9998 / 0,9999 / 0,9961 / 0,9914 / 0,9828 / 0,9397.

## Interprétation (hypothèses, non démontrées)
- Trois détecteurs presque équivalents en performance propre ont des robustesses très différentes face au même attaquant.
- XGBoost s'appuie surtout sur `Bwd Packet Length Std` (variable gelée) ; la forêt de la Phase 4.3 (configuration différente) donnait de l'importance à des variables recalculées par le remplissage.
  Le gain atteignable de la forêt n'a pas été mesuré.
- Les flux SSH-Patator ont presque tous le même `Fwd Packet Length Max` (environ 640 octets) : les détecteurs ont peut-être appris une signature de taille propre à l'outil. Non testé.
- La règle de sélection a départagé les détecteurs par simplicité et non par robustesse.

## Limites
- Populations différentes d'un détecteur à l'autre : comparaisons indicatives. Les médianes cachent des sous-groupes.
- La régression logistique rate déjà une partie des Slowloris et Slowhttptest sans perturbation (rappel avant attaque de 0,83 et 0,88).
- Une seule graine, 300 flux par famille, validation seulement ; attaque dans l'espace des caractéristiques, variables Bwd gelées.
- Reproductibilité de cette exécution non vérifiée par une seconde exécution.

## Planifié
- Durcissement par entraînement adverse, évalué sur les quatre états (voir `docs/hardening_specification.md`).