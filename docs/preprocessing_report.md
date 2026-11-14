\# Rapport de preprocessing (Phase 4.1)



\*\*Observé\*\* = mesuré par `src/data/check\_preprocessing\_real.py` (train et validation uniquement).

\*\*Planifié\*\* = pas encore exécuté. Le vendredi n'a pas été chargé. Aucun modèle n'a été entraîné.



\## Observé



| | Train (lun+mar+mer) | Validation (jeudi) |

|---|---|---|

| Lignes | 1 190 343 | 362 076 |

| Cible 0 (normal + attempted) | 1 011 765 | 290 169 |

| Cible 1 (attaque effective) | 178 578 (15,00 %) | 71 907 (19,86 %) |

| Header négatif Fwd / Bwd | 170 / 255 | 99 / 128 |



\- Aucun label inconnu : le mapping couvre tous les labels de ces deux splits.

\- Train : DoS, Patator, Heartbleed (DoS Hulk = 88,7 % des attaques).

\- Validation : Infiltration - Portscan = 71 767 sur 71 907 attaques (99,8 %).

&#x20; Train et validation ne partagent aucune famille d'attaque.

\- Matrices transformées finies : 85 colonnes (stratégie `impute`) ou 83 (`exclude`).

\- Seule `Protocol` est traitée comme catégorielle.

\- Mémoire : 1,25 GiB pour le train, 46 s au total. Pas de chunking nécessaire.



\## Décisions

\- Ports exclus de X par défaut (artefacts de laboratoire). Sensibilité à tester plus tard.

\- `Protocol` traité comme catégorielle (one-hot, catégories inconnues ignorées).

\- Stratégies A (impute) et B (exclude) comparées en Phase 4.2 sur la validation.



\## Limites

\- Le découpage mesure un décalage combiné jour + famille d'attaque.

\- Le rappel agrégé sur la validation est dominé par le portscan : à rapporter par famille.

\- L'hypothèse de débordement int16 sur les headers n'est pas confirmée.

