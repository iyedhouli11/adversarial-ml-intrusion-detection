# Faisabilité des perturbations par famille (segment train)

**Observé** = mesuré par `src/attacks/check_perturbation_by_family.py`.
Données : segment train de lundi à mercredi (intervalle 1 %), 105 364 flux d'attaque effective. Aucun modèle interrogé.
Validation, test, jeudi et vendredi non chargés. Bornes min/max calculées sur toutes les lignes du train.
Règle MTU appliquée dans la mesure seulement : candidat rejeté si `Fwd Packet Length Max` > 1 500 octets (0 % des attaques du train dépassent 1 500).

## Observé

Plus grand facteur de remplissage avant le MTU (quantiles 5 / 50 / 95 %) : Hulk 3,750 / 4,298 / 4,983 ; GoldenEye 2,493 / 3,722 / 5,190 ;
Slowhttptest 2,885 / 2,885 / 214,286 ; Slowloris 6,494 / 6,494 / 187,500 ; FTP-Patator 50,000 / 65,217 / 75,000 ; SSH-Patator 2,344 / 2,344 / 2,344 ;
Heartbleed 8,849 / 22,727 / 22,727.

Part de candidats rejetés (toutes règles, MTU inclus), remplissage seul :

| Famille | A=0,1 | A=0,25 | A=0,5 | A=1 | A=2 |
|---|---|---|---|---|---|
| DoS GoldenEye | 0 | 0 | 0 | 0,0016 | 0,1837 |
| DoS Hulk | 0 | 0 | 0 | 0 | 0 |
| DoS Slowhttptest | 0 | 0 | 0 | 0 | 0,6631 |
| DoS Slowloris | 0 | 0 | 0 | 0 | 0 |
| FTP-Patator | 0 | 0 | 0 | 0 | 0 |
| SSH-Patator | 0 | 0 | 0 | 0,0006 | 1,0000 |

Part de candidats rejetés, délai seul :

| Famille | A=0,1 | A=0,25 | A=0,5 | A=1 | A=2 |
|---|---|---|---|---|---|
| DoS GoldenEye | 0,0513 | 0,0909 | 0,1404 | 0,2029 | 0,2968 |
| DoS Hulk | 0,0000 | 0,0001 | 0,0001 | 0,0001 | 0,0027 |
| DoS Slowhttptest | 0,3350 | 0,6271 | 0,6456 | 0,6456 | 0,6972 |
| DoS Slowloris | 0,0316 | 0,8138 | 0,8138 | 0,8142 | 0,8393 |
| FTP-Patator | 0 | 0 | 0 | 0 | 0 |
| SSH-Patator | 0 | 0 | 0 | 0 | 0 |

Colonnes hors bornes, délai seul, A = 0,25 : Slowloris `Fwd IAT Total` et `Flow Duration` 0,8138, `Fwd IAT Max` 0,3575 ;
Slowhttptest `Fwd IAT Total` et `Flow Duration` 0,6271, `Fwd IAT Max` 0,5278 ; GoldenEye `Fwd IAT Total` et `Flow Duration` 0,0909, `Fwd IAT Max` 0,0531.
Heartbleed (7 flux) est rejeté dans tous les cas de délai : aucune conclusion.

## Interprétation (hypothèses, non démontrées)
- Les DoS lents sont proches du maximum de durée observé (hypothèse : délai d'expiration des flux à environ 120 s) ; l'allongement des intervalles
  les fait sortir des bornes. À tester directement.
- La borne utilisée est le maximum observé sur le train, un proxy prudent et non une limite physique démontrée.
- Le remplissage est faisable jusqu'à un facteur 2 pour toutes les familles ; au-delà, le MTU bloque SSH-Patator et Slowhttptest.

## Limites
- Attaque dans l'espace des caractéristiques ; les variables non recalculables sont gelées.
- Mesure sur le train : la faisabilité sur la validation peut différer.
- Aucun score de détecteur n'a été mesuré : cette étape ne dit rien sur l'évasion.