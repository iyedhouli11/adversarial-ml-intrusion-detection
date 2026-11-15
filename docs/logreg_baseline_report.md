# Baseline régression logistique (Phase 4.2)

**Observé** = mesuré par `src/models/logreg_baseline.py` et `src/models/logreg_threshold_diagnostic.py`.
Entraînement : lundi à mercredi. Évaluation : jeudi (validation). Le vendredi n'a pas été chargé.
Paramètres : valeurs par défaut de scikit-learn, `max_iter=500`, graine 42, seuil 0,5. Une seule exécution.

## Observé : baseline au seuil 0,5

| | A (`impute`) | B (`exclude`) |
|---|---|---|
| TN / FP | 289 867 / 302 | 289 853 / 316 |
| FN / TP | 66 304 / 5 603 | 66 254 / 5 653 |
| Précision | 0,9489 | 0,9471 |
| Rappel | 0,0779 | 0,0786 |
| F1 | 0,1440 | 0,1452 |
| PR-AUC (référence aléatoire 0,1986) | 0,5974 | 0,6091 |
| Itérations (max 500) | 113 | 102 |
| Entraînement / inférence jeudi | 23,1 s / 0,14 s | 27,2 s / 0,12 s |

- Le détecteur lève peu d'alertes (165 pour 10 000 flux) et rate la grande majorité des attaques.
- `Infiltration - Portscan` représente 71 767 des 71 907 attaques de jeudi ; 7,8 % sont détectées.
- Les familles web et infiltration ont 13 à 73 flux : trop peu pour conclure.

## Observé : diagnostic du seuil (stratégie B, validation uniquement)

| Seuil | Alertes / 10 000 | Précision | Rappel portscan | BENIGN signalés |
|---|---|---|---|---|
| 0,5 | 165 | 0,9471 | 0,0788 | 0,0011 |
| 0,3 | 255 | 0,9395 | 0,1209 | 0,0019 |
| 0,1 | 656 | 0,8973 | 0,2969 | 0,0084 |
| 0,05 | 907 | 0,8611 | 0,3939 | 0,0157 |
| 0,01 | 1 532 | 0,7574 | 0,5853 | 0,0465 |
| 0,001 | 2 197 | 0,5303 | 0,5873 | 0,1291 |

- Le rappel plafonne vers 0,59 : environ 41 % des flux de portscan ont un score inférieur à 0,001.
- Quantiles des scores du portscan (5, 25, 50, 75, 95 %) : 0,0000 ; 0,0000 ; 0,0360 ; 0,1205 ; 0,9927.
- Quantiles du BENIGN : 0,0000 ; 0,0000 ; 0,0000 ; 0,0000 ; 0,0086.
- Aucun seuil n'est retenu.

## Coût des faux positifs et des faux négatifs
- Un faux négatif est une attaque non détectée : risque principal, ici très fréquent.
- Un faux positif consomme du temps d'analyste. À 0,01, environ 13 400 flux BENIGN de jeudi seraient signalés (fatigue d'alerte).

## Limites
- Une seule graine et une seule exécution ; aucune variabilité mesurée.
- Les stratégies A et B diffèrent de 0,0117 en PR-AUC : aucune conclusion.
- Jeudi est dominé par le portscan, absent de l'entraînement : les mesures décrivent surtout cette famille.
- Hypothèse non testée : le modèle linéaire ne distingue pas une partie du portscan du trafic normal.
- Les précisions à bas seuil dépendent de la proportion d'attaques de jeudi (19,86 %).

## Planifié
- Random Forest (4.3) et XGBoost (4.4) avec le même protocole, pour tester l'hypothèse ci-dessus.
- Décision sur le découpage par jour à réévaluer avec ces résultats, sans utiliser le vendredi.