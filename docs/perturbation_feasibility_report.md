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

## Gain du détecteur atteignable par la perturbation (segment train)

**Observé** (`src/attacks/reachable_gain.py`). XGBoost max_depth 3, n_estimators 100, graine 42, ajusté sur le segment train ; importances en gain.
Validation, test, jeudi et vendredi non chargés. Contrôle : gain total 1,0000 et `Bwd Packet Length Std` 0,5572 (valeur déjà observée).

- Gain sur les colonnes changées ou recalculées : 0,1535 ; sur les colonnes gelées : 0,8465.
- Atteignables : `Packet Length Mean` 0,0550 ; `Packet Length Std` 0,0431 ; `Fwd IAT Max` 0,0331 ; `Flow Duration` 0,0085 ; `Flow Bytes/s` 0,0051.
- Gelées : `Bwd Packet Length Std` 0,5572 ; `Bwd IAT Max` 0,0415 ; `Fwd Seg Size Min` 0,0315 ; `Bwd Packet Length Mean` 0,0265 ; `Bwd IAT Mean` 0,0227 ; `Down/Up Ratio` 0,0182.
- Maximum de `Flow Duration` et de `Fwd IAT Total` dans le train : 1,2e8 us (120 s).
- Part des flux d'attaque au-dessus de 80 % de ce maximum / au-dessus de 99 % : Slowloris 0,8138 / 0,0004 ; Slowhttptest 0,6271 / 0,0175 ;
  GoldenEye 0,0909 / 0,0034 ; Hulk 0,0001 / 0 ; Patator ≈ 0.

## Interprétation (hypothèses, non démontrées)
- Les parts à 80 % égalent les taux de rejet à A = 0,25 : c'est arithmétique (1,25 x 0,8 = 1), non une preuve d'un délai d'expiration.
- Un maximum exact de 120 s est compatible avec un délai d'expiration des flux, sans le démontrer.
- L'importance en gain est une statistique d'entraînement, pas une mesure de sensibilité par flux ; les variables corrélées partagent le crédit.
- `Fwd Seg Size Min` et `Down/Up Ratio` restent gelées pour ne pas élargir la surface d'attaque après avoir vu les résultats ;
  elles sont des variantes de sensibilité à étiqueter comme choix post hoc.

*Cette section a été ajoutée après l'exécution de l'attaque d'évasion (voir `docs/attack_specification.md`, version 1).*