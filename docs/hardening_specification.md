# Spécification du durcissement (version 1)

**Statut** : rédigée et commitée avant l'écriture et l'exécution de tout script de durcissement. Aucune expérience de durcissement n'a été exécutée.
Toute modification ultérieure sera datée et étiquetée post hoc.

## Contexte et décisions
- Cible principale pré-déclarée : XGBoost (règle déclarée du réglage). Son évasion réaliste est quasi nulle (2/1 800) : le durcissement n'a presque rien à mesurer.
- **Post hoc** (décidé après avoir vu `docs/multi_target_attack_report.md`) : durcir aussi la forêt et la régression logistique, qui montrent des évasions mesurables
  (SSH-Patator surtout). Les trois configurations restent celles de la règle déclarée, sans nouveau réglage, graine 42. Ce choix n'est pas fait sur la robustesse.

## Exemples adverses (entraînement adverse, un seul tour)
- Source : flux d'attaque effective du segment **train** uniquement (105 364 flux). Jamais la validation, le test, le jeudi ni le vendredi.
- Pour chaque flux : jusqu'à 20 tirages (s, t) uniformes dans [1, 2] x [1, 2] (A_train = 1) ; on garde le premier candidat réalisable
  (bornes min/max du train, ordres vérifiés, valeur finie, `Fwd Packet Length Max` <= 1 500) ; aucun candidat réalisable : pas d'exemple, compté.
- Étiquette 1 ; une copie adverse par flux au plus (K = 1), ajoutée à l'entraînement. La part d'attaques passe d'environ 15 % à 26 % au plus.
- Aucune requête au modèle pour fabriquer les exemples : augmentation par perturbations réalisables, pas d'adversaire adaptatif.
- Le prétraitement reste ajusté sur le train original ; les exemples adverses sont transformés avec lui. Réentraînement depuis zéro, mêmes hyperparamètres.

## Évaluation : quatre états par détecteur
1. original propre ; 2. original sous attaque ; 3. durci propre ; 4. durci sous attaque.
- **Propre** (validation, seuil 0,5) : précision, rappel, F1, PR-AUC, FP, FN, temps d'entraînement.
- **Sous attaque** : (a) recherche aléatoire avec une nouvelle graine (1234), mêmes amplitudes, même budget de 1 000 requêtes ;
  (b) grille déterministe 31 x 31 sur [1, 3] x [1, 3] ; l'amplitude A = 2 dépasse A_train = 1 (force non vue à l'entraînement).
- **Population d'évasion** : flux détectés par le modèle évalué, au plus 300 par famille, graine 42 (comme l'attaque initiale).
- **Rappel sous attaque sur population commune** : 300 flux par famille tirés parmi toutes les attaques effectives de validation (graine 42), identiques pour tous les modèles ;
  un flux manqué au départ ou évadé compte comme manqué. Heartbleed (2 flux) rapporté mais non interprété.
- Intervalles de Wilson à 95 %. Un durcissement n'est déclaré efficace pour une famille que si les intervalles avant et après ne se chevauchent pas.
  Le coût sur la performance propre est rapporté dans tous les cas.

## Ce qui n'est pas testé (limites déclarées d'avance)
Attaquant adaptatif qui connaît la défense ; autres familles de perturbation (ajout de paquets, variables Bwd) ; transfert entre modèles ; plusieurs graines d'entraînement ;
segment test et vendredi (isolés jusqu'à l'évaluation finale). Les familles de perturbation de l'évaluation sont les mêmes que celles de l'entraînement :
le durcissement est évalué contre l'attaque connue (nouvelle graine, autre méthode de recherche, force supérieure), pas contre un attaquant inconnu.

## Contrôles
Identité s = t = 1 pour chaque modèle ; nombre d'exemples adverses fabriqués et part de flux sans candidat réalisable ; part d'attaques dans l'entraînement avant et après.