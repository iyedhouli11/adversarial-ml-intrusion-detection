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