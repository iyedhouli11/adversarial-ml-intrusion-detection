# Attaque d'évasion par recherche aléatoire : premiers résultats (Phase 5)

**Observé** = mesuré par `src/attacks/random_search_attack.py` (spécification v1, `docs/attack_specification.md`).
Cible : XGBoost (max_depth 3, 100 arbres, learning_rate 0,1, graine 42) ajusté sur le segment train, seuil 0,5.
Population : flux de validation d'attaque effective détectés à 0,5, 300 par famille (graine 42), soit 1 800 flux ; Heartbleed exclu (0 détecté).
Segment test, jeudi et vendredi non chargés. Une seule exécution, aucun réglage de l'attaque.

## Contrôle d'identité
s = t = 1 : écart maximal de score 0, 0 ligne avec un écart supérieur à 1e-6, 0 bascule sous 0,5.

## Observé

Taux d'évasion : 0/300 pour toutes les familles et toutes les amplitudes (intervalle de Wilson à 95 % : 0 à 1,26 %),
sauf DoS Slowhttptest à A = 1 et A = 2 : 2/300 = 0,67 % (0,18 à 2,40 %). Au total 2 flux évadés sur 1 800 à A = 1 et à A = 2.

| Famille | Rappel validation avant attaque | Score médian initial | Score minimal médian à A = 2 |
|---|---|---|---|
| DoS GoldenEye | 0,9816 | 0,9999 | 0,9998 |
| DoS Hulk | 0,9998 | 0,9999 | 0,9999 |
| DoS Slowhttptest | 0,9936 | 0,9972 | 0,9961 |
| DoS Slowloris | 1,0000 | 0,9970 | 0,9914 |
| FTP-Patator | 1,0000 | 0,9970 | 0,9828 |
| SSH-Patator | 1,0000 | 0,9944 | 0,9397 |

- Slowhttptest : à A = 1, requêtes 43 (médiane) et 61 (maximum) ; à A = 2, 2 requêtes. Rappel après attaque estimé sur l'échantillon : 0,9870 (avant : 0,9936).
- Aucune évasion pour les autres combinaisons famille x amplitude.
- La part de flux avec au moins un candidat réalisable vaut 1,0 partout : non informative (un candidat proche de l'identité est toujours réalisable).

## Interprétation (hypothèses, non démontrées)
- Les scores bougent peu : cohérent avec 84,65 % du gain sur des colonnes gelées, sans prouver un lien causal.
- Les deux flux évadés sont peut-être les moins confiants de Slowhttptest (quantile 5 % des scores détectés : 0,7587) ; non vérifié.
- Une faible évasion est un résultat conjoint du détecteur et du modèle de menace ; ce n'est pas une preuve de robustesse.

## Limites
- Espace de perturbation à deux paramètres : 2 000 tirages le couvrent presque entièrement, le plafond de 1 000 requêtes ne contraint pas.
- Les tirages aléatoires peuvent manquer des coins ou des arêtes du domaine : à vérifier par une grille déterministe.
- Échantillon de 300 flux par famille ; le rappel après attaque est une estimation.
- La spécification v1 n'était pas commitée avant la première exécution : elle est enregistrée rétroactivement (voir docs/attack_specification.md). Ses paramètres sont ceux du script, mais l'historique Git ne prouve pas qu'ils ont été fixés avant de voir les résultats.
- Attaque dans l'espace des caractéristiques ; variables non recalculables gelées ; mesure sur la validation uniquement.

## Planifié
- Grille déterministe pour vérifier que la recherche n'a pas manqué d'évasions ; relance pour vérifier la reproductibilité.
- Décision sur la suite (cibles alternatives, scénario élargi étiqueté non réaliste) avant le durcissement.