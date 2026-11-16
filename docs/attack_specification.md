# Spécification de l'attaque d'évasion (provisoire)

**Statut** : provisoire, à figer dans un commit dédié avant la première exécution de l'attaque. Aucune attaque n'a été exécutée.

## Cible
XGBoost (max_depth 3, n_estimators 100, learning_rate 0,1, tree_method hist, graine 42), stratégie `exclude`, ajusté sur le segment train, seuil 0,5.

## Population attaquée
- Flux de validation de cible 1 avec score >= 0,5 (32 108 observés). Heartbleed (0 détecté) est exclu.
- Échantillon : au plus 300 flux par famille, tirés avec la graine 42 parmi les flux détectés (6 familles, au plus 1 800 flux).
  Justification : coût de calcul et lisibilité ; les effectifs sont affichés et les intervalles de confiance rapportés.

## Accès et budget
Boîte noire à score ; au plus 1 000 requêtes par flux ; nombre de requêtes enregistré (médiane et maximum).

## Perturbation (espace des caractéristiques uniquement)
Deux facteurs indépendants, côté Fwd seulement, tirés dans [1, 1 + A] :
- **s** (remplissage) : toutes les longueurs de paquets Fwd sont multipliées par s ; une longueur nulle reste nulle.
- **t** (dilatation temporelle) : tous les intervalles Fwd sont multipliés par t.
- Amplitudes A à balayer : 0,1 ; 0,25 ; 0,5 ; 1 ; 2.
- Chaque valeur reste dans les bornes min/max observées sur le segment train.

Variables gelées : variables `Bwd`, flags, protocole, ICMP, `Total TCP Flow Time`, `Active*`, `Idle*`, `Bulk*`, `Subflow*`, statistiques IAT du flux
non recalculables. Ports et `Header Length` sont hors du modèle.

Variables dérivées recalculées avec les formules vérifiées : totaux, débits, `Down/Up Ratio`, `Packet Length Mean/Max/Min/Std/Variance`,
copies exactes, `Flow IAT Mean`, `Fwd/Bwd IAT Mean`, compteurs PSH et RST.

**Hypothèse de modélisation, à vérifier** : l'allongement des intervalles Fwd allonge le flux de la même durée
(`Flow Duration' = Flow Duration + (t - 1) x Fwd IAT Total`).

Les candidats qui violent les bornes d'ordre vérifiées (par exemple `Flow IAT Min <= Mean <= Max`, `Fwd IAT Total <= Flow Duration`) sont rejetés et comptés.

## Mesures
Taux d'évasion par famille (flux du dénominateur dont un candidat réalisable obtient un score < 0,5) ; courbe taux d'évasion contre amplitude ;
requêtes (médiane, maximum) ; taux de rejet ; intervalles de confiance sur les petits effectifs.

## Contrôles
- Test d'identité : A = 0 reproduit les vecteurs d'origine.
- Les échantillons originaux ne sont jamais modifiés.
- Développement sur la validation uniquement ; segment test, jeudi et vendredi non utilisés.

## Limites
Attaque dans l'espace des caractéristiques, pas au niveau des paquets. Hypothèse « attaquant = client » non prouvée. Une seule graine.
Une réussite ne dit rien sur les familles non attaquées, et un échec peut venir du modèle de menace (variables `Bwd` interdites) et non du détecteur.

## Version 1, enregistrée rétroactivement

**Provenance** : cette version a été rédigée par l'auteur avant la première exécution de l'attaque, mais elle n'a **pas** été commitée avant celle-ci.
Le premier commit qui contient le script d'attaque et ses résultats précède l'enregistrement de cette version. Ses paramètres sont ceux
implémentés dans `src/attacks/random_search_attack.py` ; l'historique Git ne prouve pas qu'ils ont été fixés avant de voir les résultats.
Toute modification ultérieure sera datée et étiquetée comme post hoc.

- **Cible** : XGBoost (max_depth 3, n_estimators 100, learning_rate 0,1, hist, graine 42) ajusté sur le segment train, seuil 0,5.
- **Population** : flux de validation de cible 1 avec score >= 0,5 ; au plus 300 par famille, tirés sans remise avec la graine 42 ; Heartbleed exclu (0 détecté).
- **Perturbation** : s (remplissage Fwd) et t (délai Fwd) tirés indépendamment et uniformément dans [1, 1 + A] ; A dans {0,1 ; 0,25 ; 0,5 ; 1 ; 2}.
- **Recherche aléatoire** : 2 000 tirages par flux ; les candidats réalisables sont interrogés dans l'ordre, au plus 1 000 requêtes par flux ;
  arrêt à la première évasion (score < 0,5).
- **Rejet sans requête, avec comptage** : hors des bornes min/max du train pour une colonne changée, ordre vérifié violé, valeur non finie,
  `Fwd Packet Length Max` > 1 500 octets.
- **Variables gelées** : côté Bwd, flags, protocole, ICMP, `Total TCP Flow Time`, `Active*`, `Idle*`, `Bulk*`, `Subflow*`, `Fwd Seg Size Min`,
  `Flow IAT Std/Min/Max`, `Fwd/Bwd IAT` non recalculables. Pas d'ajout de paquets.
- **Mesures** : taux d'évasion = flux évadés / flux de la population de la famille, intervalle de Wilson à 95 %, requêtes, score minimal atteint,
  rappel avant et après estimés.
- **Contrôle d'identité** : s = t = 1 doit redonner les scores d'origine.
- **Lecture** : un faible taux d'évasion est un résultat conjoint du détecteur et du modèle de menace (84,65 % du gain est gelé), pas la preuve que le
  détecteur est robuste. L'espace de recherche n'a que deux paramètres : le budget de requêtes ne contraint presque pas.
- **Correction** : la part de flux avec au moins un candidat réalisable (prévue dans la version provisoire) est toujours 1,0 et n'est pas informative ;
  elle est remplacée par la part de points réalisables d'une grille déterministe (`src/attacks/grid_check.py`).