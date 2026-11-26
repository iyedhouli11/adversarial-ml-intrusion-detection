# Spécification de l'évaluation finale (version 1)

**Statut** : **Planifié**. Rédigée et commitée **avant** l'écriture et l'exécution de tout script d'évaluation finale. Le segment test du découpage par strate et le vendredi n'ont jamais été lus par un modèle.
Toute modification ultérieure sera datée et étiquetée post hoc.

## Principe

- Deux évaluations, chacune exécutée **une seule fois**, dans cet ordre :
  1. **Évaluation principale** : segment `test` du découpage par strate (lundi à mercredi, dernier 20 % de chaque couple (jour, label), 226 157 lignes).
  2. **Étude du décalage** : vendredi, à part, exécuté seulement après l'enregistrement des résultats de l'évaluation principale.
- Rien n'est réglé, choisi ni corrigé à partir de ces résultats. Si un bogue est découvert après coup, la correction est datée, étiquetée post hoc, et les deux résultats (avant et après correction) sont rapportés.
- Le choix du découpage par strate reste **post hoc** (décidé après les résultats du jeudi) : le résultat principal est une borne optimiste.

## Modèles gelés (six)

- Configurations de la règle de réglage déclarée : régression logistique `C = 0,1` ; forêt aléatoire 100 arbres, `min_samples_leaf = 20` ; XGBoost profondeur 3, 100 arbres. Graine 42, seuil 0,5.
- Pour chacune : la version **originale** et la version **durcie** (procédure de `docs/hardening_specification.md`, A_train = 1, K = 1).
- Entraînement sur le segment `train` seulement (pas train + validation), pour évaluer exactement les modèles étudiés sur la validation. Prétraitement ajusté sur le train original.
- Contrôle : les FP/FN sur la validation doivent être identiques à ceux déjà mesurés (régression logistique 509/274 et 444/227 ; forêt 11/40 et 12/26 ; XGBoost 7/36 et 5/10). Un écart est signalé avant de lire le test.

## Mesures sur chaque segment

**Propre** (seuil 0,5) : matrice de confusion, précision, rappel, F1, PR-AUC, FP, FN ; rappel par famille ; temps d'inférence (une seule mesure, signalée comme bruitée, non comparée). L'accuracy n'est pas utilisée.

**Sous attaque** : même modèle de menace et même attaque que sur la validation (côté `Fwd` seulement, remplissage `s` et délai `t`, variables dérivées recalculées, règle de réalisme, `Fwd Packet Length Max` <= 1 500).
- Recherche aléatoire, graine 1234, amplitudes (0,1 ; 0,25 ; 0,5 ; 1 ; 2), budget 1 000 requêtes par flux.
- Grille déterministe 31 x 31 sur [1, 3] x [1, 3].
- Population d'évasion : flux d'attaque détectés par le modèle évalué, au plus 300 par famille, graine 42. Mesures : taux d'évasion (Wilson 95 %), requêtes médiane et maximale des flux évadés.
- Rappel sous attaque sur population commune : au plus 300 flux par famille parmi toutes les attaques effectives du segment (graine 42), identiques pour les six modèles ; un flux manqué au départ ou évadé compte comme manqué.
- **Courbe exigée** : rappel sur population commune selon l'amplitude (A = 0 puis les cinq amplitudes), original et durci, pour chaque détecteur.

**Flux BENIGN perturbés** (contrôle déclaré d'avance cette fois) : 20 000 flux BENIGN du segment, `s` et `t` tirés dans `1 + A·U(0, 1)`, amplitudes (0,5 ; 1 ; 2), graine 99, candidats réalisables seulement ; part signalée comme attaque pour les six modèles.

## Règles de lecture

- Une famille avec moins de 30 flux est rapportée mais non interprétée.
- Un durcissement est dit efficace pour une famille seulement si les intervalles de Wilson avant et après ne se chevauchent pas. Le coût sur la performance propre est rapporté dans tous les cas.
- Vendredi : la cible et le prétraitement sont les mêmes ; aucune hypothèse n'est faite d'avance sur les familles présentes. Les familles absentes du train sont signalées comme telles. Le vendredi mesure la généralisation hors distribution, pas la robustesse adverse.

## Sorties

- Agrégats seulement (aucune donnée brute) dans `results/final/` : un CSV par mesure et par segment (propre, par famille, évasion, rappel selon l'amplitude, BENIGN perturbés), plus la sortie console complète enregistrée dans un fichier texte.
- `.gitignore` ignore `*.csv` : une exception limitée à `results/` sera ajoutée et commitée avant l'exécution.
- Rapport `docs/final_evaluation_report.md` écrit à partir de ces fichiers.

## Ce qui n'est pas testé (limites déclarées d'avance)

Attaquant adaptatif qui connaît la défense ; autres perturbations (ajout de paquets, variables `Bwd`) ; plusieurs graines d'entraînement ; transfert entre modèles ; le jeudi n'est pas réévalué.