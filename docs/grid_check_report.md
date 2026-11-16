# Vérification par grille de la recherche d'évasion (Phase 5)

**Observé** = mesuré par `src/attacks/grid_check.py`. Même cible et même construction de population que `random_search_attack.py`
(graine 42, 300 flux par famille, 1 800 flux, Heartbleed exclu). Grille déterministe 31 x 31 sur [1, 3] x [1, 3] (A = 2, qui contient les amplitudes plus petites),
plus un axe de remplissage seul et un axe de délai seul ; au plus 961 requêtes par flux. Aucun réglage. Segment test, jeudi et vendredi non chargés. Une seule exécution.

## Observé
Taux d'évasion : 2/300 (0,67 %, Wilson 95 % : 0,18 à 2,40 %) pour DoS Slowhttptest en grille complète et en remplissage seul ;
0/300 (borne haute de Wilson 1,26 %) pour toutes les autres familles ; délai seul : 0 évasion partout.

Part des points de grille réalisables (règles de rejet et MTU 1 500 inclus) :

| Famille | Grille complète | Remplissage seul | Délai seul |
|---|---|---|---|
| DoS GoldenEye | 0,7919 | 0,9569 | 0,8210 |
| DoS Hulk | 0,9995 | 1,0000 | 0,9995 |
| DoS Slowhttptest | 0,1998 | 0,9942 | 0,2056 |
| DoS Slowloris | 0,2406 | 1,0000 | 0,2406 |
| FTP-Patator | 1,0000 | 1,0000 | 1,0000 |
| SSH-Patator | 0,6774 | 0,6774 | 1,0000 |

Chute médiane de score (score initial moins score minimal atteint), grille complète / remplissage seul / délai seul :
GoldenEye 0,0000 / 0,0000 / 0,0000 ; Hulk 0,0000 / 0,0000 / 0,0000 ; Slowhttptest 0,0011 / 0,0011 / 0,0000 ;
Slowloris 0,0056 / 0,0056 / 0,0000 ; FTP-Patator 0,0142 / 0,0142 / 0,0004 ; SSH-Patator 0,0547 / 0,0547 / 0,0006.
Score minimal médian atteint (grille complète) : 0,9998 ; 0,9999 ; 0,9961 ; 0,9914 ; 0,9828 ; 0,9397 (même ordre de familles).

## Interprétation (hypothèses, non démontrées)
- La grille trouve autant d'évasions que la recherche aléatoire (2 contre 2) : la recherche n'était pas le facteur limitant dans cet espace.
  L'identité des flux évadés n'est pas comparée.
- Les évasions viennent du remplissage ; le délai ne déplace presque pas le score.
- La faisabilité réduit surtout la boîte pour les DoS lents (délai, bornes de durée) et pour SSH-Patator (MTU).

## Limites
- Attaquant à deux paramètres, limité aux variables Fwd ; la grille ne couvre que la boîte A = 2.
- Échantillon de 300 flux par famille, une seule graine, validation seulement.
- Un attaquant faible ne prouve pas que le détecteur est robuste.