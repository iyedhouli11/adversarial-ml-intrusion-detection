# Rapport : durcissement par entraînement adverse (Phase 6)

## Provenance des chiffres

**Observé**, avec une réserve : les chiffres ci-dessous viennent de la sortie console de `src/defenses/adversarial_training.py` et de `src/defenses/benign_perturbation_check.py` (commit `0df3293`), lors d'une exécution précédente. Les scripts affichent leurs résultats sans les sauvegarder, et cette sortie n'a pas été archivée : les chiffres ont été recopiés dans `docs/PROJECT_HANDOFF.md`, section 9.

## Protocole

Spécification : `docs/hardening_specification.md`, commitée (`31c2cce`) **avant** tout script de durcissement.

- Pour chaque flux d'attaque du **train**, une copie adverse réalisable : 20 tirages de `(s, t)` dans `[1, 2]²`, premier candidat réalisable retenu.
- 105 045 copies ajoutées ; 319 flux sans candidat réalisable. Part d'attaques dans le train : 15,00 % avant, 26,06 % après.
- Réentraînement depuis zéro des trois détecteurs retenus (régression logistique, forêt aléatoire, XGBoost), seuil 0,5, selon la spécification.
- Évaluation sur la validation en 4 états : original, original sous attaque, durci, durci sous attaque. Attaques : recherche aléatoire (graine 1234) et grille déterministe, amplitude jusqu'à A = 2 (amplitude d'entraînement A_train = 1).

## Résultats

### Rappel sur la population commune (poolé sur les familles)

Format : propre / recherche aléatoire A = 2 / grille.

| Détecteur | Original | Durci |
|---|---|---|
| Régression logistique | 0,9373 / 0,6465 / 0,4911 | 0,9467 / 0,9273 / 0,9256 |
| Forêt aléatoire | 0,9939 / 0,8269 / 0,8252 | 0,9950 / 0,9945 / 0,9945 |
| XGBoost | 0,9950 / 0,9945 / 0,9945 | 0,9989 / 0,9983 / 0,9983 |

### Performance propre sur la validation (seuil 0,5)

| Détecteur | FP / FN original | FP / FN durci |
|---|---|---|
| Régression logistique | 509 / 274 | 444 / 227 |
| Forêt aléatoire | 11 / 40 | 12 / 26 |
| XGBoost | 7 / 36 | 5 / 10 |

La performance propre ne baisse pas. Les temps d'entraînement ne sont pas rapportés : ils varient avec la charge de la machine.

### Taux d'évasion

Sur les 42 combinaisons (détecteur, famille, attaque) où une évasion a lieu : 24 sont « améliorées » (intervalles de Wilson à 95 % séparés), 18 non séparées. La régression logistique durcie garde 10,7 % d'évasion sur SSH-Patator à A = 2, et 5,7 % à A = 1, donc dans la boîte d'entraînement.

## Contrôle post hoc (hors spécification)

**Post hoc** : ajouté après avoir vu les résultats du durcissement (`benign_perturbation_check.py`).

- 20 000 flux BENIGN de la validation, perturbés avec `s` et `t` tirés dans `1 + A·U(0, 1)` (candidats réalisables seulement). Part signalée comme attaque, sur les amplitudes testées jusqu'à A = 2 : régression logistique durcie, de 0,24 % à 2,35 % ; régression logistique originale, de 0,21 % à 0,51 % ; forêt et XGBoost : 0.
- Changements appariés de prédiction sur toute la validation, original vers durci : attaques gagnées 52 / 14 / 26 et perdues 5 / 0 / 0 (régression logistique / forêt / XGBoost).

**Hypothèse** : la régression logistique durcie aurait en partie appris « perturbation = attaque », ce qui augmente les faux positifs sur des flux normaux perturbés.

## Limites

- Évalué contre **l'attaque connue** (mêmes variables, même famille de perturbations), pas contre un attaquant adaptatif qui connaîtrait la défense. Ce n'est pas une preuve de robustesse.
- Une seule graine d'entraînement.
- La validation a déjà servi au réglage et au choix du protocole : borne optimiste.
- **Hypothèse** non testée : l'amélioration du rappel propre viendrait de l'augmentation de données ou du rééquilibrage des classes.
- Le segment test et le vendredi n'ont pas été utilisés.