# Feature Controllability Audit — Individual Work

**Statut : grille préparatoire ; les colonnes exactes seront confirmées après inspection des fichiers CIC-IDS2017.**

## Objectif

Déterminer ce qu'un attaquant peut modifier dans un flux sans supposer qu'une valeur numérique est librement manipulable. Cette analyse définit les contraintes de l'attaque, mais ne décide pas seule quelles variables le détecteur peut utiliser.

## Distinction obligatoire

Deux décisions indépendantes doivent être documentées :

1. **Inclusion dans le détecteur** : la variable est-elle observable, utile et exempte de fuite ou d'artefact ?
2. **Contrôlabilité par l'attaquant** : la variable peut-elle être modifiée sans coût, avec coût, ou seulement en changeant/détruisant l'attaque ?

Ainsi, une variable non modifiable n'est pas automatiquement supprimée du détecteur. Elle est seulement placée dans le masque des variables interdites pour l'attaque.

## Catégories finales

| Catégorie | Signification |
|---|---|
| Librement modifiable | Modification plausible sans changer l'objectif de l'attaque, sous réserve de cohérence |
| Modifiable avec un coût | Modification possible mais nécessitant du temps, des paquets, des ressources ou un compromis opérationnel |
| Non modifiable sans détruire ou changer l'attaque | Variable observée mais non contrôlable dans le scénario retenu |

Une quatrième valeur **à vérifier** sera utilisée temporairement pendant l'audit ; elle ne pourra pas rester dans le modèle de menace final.

## Groupes à examiner

| Groupe | Inclusion dans le détecteur | Contrôlabilité initiale à vérifier |
|---|---|---|
| Flow ID, IP, ports, timestamps | Décision séparée selon risque d'artefact | Souvent non modifiable ou sémantiquement déterminant |
| Durée, paquets et octets | Candidats possibles | Généralement modifiables avec coût et dépendances |
| Débits, moyennes et intervalles | Candidats possibles | Variables dérivées ; ne pas modifier indépendamment |
| Protocoles, états et flags | Candidats possibles | Souvent liés au service ou à l'attaque |
| TTL, fenêtres et compteurs | Candidats possibles | Coût, dépendances ou impossibilité selon le scénario |
| Agrégats de connexions | À auditer pour fuite | Dépendent d'autres flux et de l'horizon d'observation |

Cette table est une hypothèse de travail, pas une autorisation de perturbation.

## Fiche par variable

Pour chaque colonne réelle, documenter : nom, définition, type, source, variable dérivée ou non, relations connues, observabilité, inclusion dans le détecteur, catégorie de contrôlabilité, coût, borne, règle de cohérence et justification.

## Limite de représentation

L'attaque prévue modifie des vecteurs de caractéristiques. Elle ne reconstruit pas les paquets ni ne recalcule un flux à partir d'une capture. Les résultats seront donc décrits comme des attaques dans l'espace des caractéristiques. Toute affirmation de réalisme réseau nécessitera une reconstruction et une vérification indépendantes.

## Critères d'acceptation

- toutes les colonnes du fichier retenu sont classées ;
- inclusion modèle et contrôlabilité sont séparées ;
- les relations entre compteurs, débits et moyennes sont testées ;
- le masque d'attaque est figé avant l'évaluation finale ;
- les échantillons incohérents sont rejetés et comptés.

## Organisation du travail

Cette analyse est réalisée individuellement après l'inspection du schéma réel et avant l'implémentation de l'attaque. Elle constitue une étape obligatoire du modèle de menace, pas une contribution séparée ou fictive.


## Inventaire et relations mesurés (segment train, lundi-mercredi)

**Observé** (`src/data/feature_inventory.py`, `src/data/feature_relations.py`). Validation, test, jeudi et vendredi non chargés.

- 80 variables en entrée (79 numériques + `Protocol`, stratégie `exclude`).
- Constantes à 0 : `Fwd URG Flags`, `Bwd URG Flags`, `URG Flag Count` ; `Subflow Bwd Packets` quasi constante.
- `ICMP Type` et `ICMP Code` sont des identifiants numériques (minimum -1), pas des mesures continues.
- 16 relations sur 17 tiennent à 0,1 % près sur toutes les lignes éligibles (erreur médiane nulle) : totaux = moyenne x nombre de paquets,
  débits = comptes / durée x 1e6 (durées en microsecondes), `Down/Up Ratio`, `Packet Length Mean` et `Max`, `Variance` = `Std`^2,
  et quatre redondances exactes (`Fwd Segment Size Avg`, `Bwd Segment Size Avg`, `Average Packet Size`, `Packet Length Variance`).
- `Total TCP Flow Time <= Flow Duration` ne tient que dans 95,63 % des lignes (environ 30 700 violations), cause non expliquée.
- Un flux de durée nulle et 18 flux sans paquet Fwd (déduits des effectifs éligibles).
- Un seul port de destination par famille d'attaque (DoS : 80 ; FTP-Patator : 21 ; SSH-Patator : 22 ; Heartbleed : 444).

**Classification provisoire** (hypothèse de travail : l'attaquant est le client qui initie le flux ; Fwd = attaquant, Bwd = serveur).

| Groupe | Variables | Catégorie provisoire | Réserve |
|---|---|---|---|
| Tailles Fwd | `Fwd Packet Length Max/Min/Mean/Std`, `Fwd Segment Size Avg`, `Fwd Seg Size Min` | avec un coût | rembourrage coûteux en bande passante ; limites du protocole applicatif |
| Volume Fwd | `Total Fwd Packet`, `Total Length of Fwd Packet` | avec un coût | le volume fait souvent partie de l'attaque |
| Rythme Fwd | `Fwd IAT Total/Mean/Std/Max/Min` | avec un coût | espacer les paquets réduit le débit d'attaque |
| Fenêtre initiale Fwd | `FWD Init Win Bytes` | à vérifier | |
| Côté serveur | variables `Bwd` | non modifiable directement | produites par la réponse du serveur |
| Protocole et flags | `Protocol`, `ICMP Type/Code`, compteurs de flags, `Fwd PSH/RST Flags` | non modifiable (à vérifier flag par flag) | définissent la nature de l'attaque |
| Dérivées vérifiées | débits, `Down/Up Ratio`, `Packet Length Mean/Max`, copies exactes | recalculées, jamais perturbées directement | formules mesurées |
| Dérivées non vérifiées | `Packet Length Std/Variance`, IAT stats, `Active/Idle`, `Bulk`, `Subflow*`, `Total TCP Flow Time` | à vérifier | pas de formule validée |
| Constantes | trois variables URG, `Subflow Bwd Packets` | sans objet | aucune information |

**Limites** : la classification est un jugement à valider, pas une mesure ; l'inclusion dans le détecteur reste une décision séparée.

## Relations mesurées, deuxième lot (segment train, lundi-mercredi)

**Observé** (`src/data/feature_relations_more.py`). Validation, test, jeudi et vendredi non chargés.

- `Packet Length Variance` = variance poolée avec correction n-1 (moyennes, écarts-types et comptes Fwd/Bwd) : tient sur 100 % des lignes ;
  la formule avec n : 8,07 %.
- `Packet Length Min` = minimum sur les directions non vides : 100 % ; `Flow IAT Mean` x (paquets-1) = `Flow Duration` : 100 % ;
  `Fwd IAT Mean` x (Fwd-1) = `Fwd IAT Total` et idem Bwd : 100 % ; `PSH`/`RST Flag Count` = somme Fwd + Bwd : 100 % ;
  `Flow IAT Min` <= Mean <= Max <= `Flow Duration` : 100 %.
- `Subflow Fwd/Bwd Bytes` ne sont pas des totaux : relation vraie sur 3,82 % / 5,50 % des lignes seulement, soit la part de zéros
  de `Total Length of Fwd/Bwd Packet` (déduction). Signification non établie.
- `Total TCP Flow Time` > `Flow Duration` : 30 658 lignes (4,37 %), toutes TCP (9,09 % des flux TCP, 0 en UDP ou autres protocoles),
  rapport médian 35,4 ; par famille : BENIGN 3,93 %, DoS Hulk 6,11 %, DoS Slowhttptest 29,02 %, DoS Slowloris 42,25 %, Patator 0 %.
  Les familles `Attempted` à 85-96 % ont 7 à 48 flux.

**Hypothèse, non testée** : `Flow Duration` plafonne à 1,2e8 us (120 s) ; `Total TCP Flow Time` monte à environ 18 900 s. Elle pourrait mesurer
la connexion entière au-delà de l'enregistrement de flux, donc dépendre d'autres flux. À tester en ablation.

**Mise à jour de la classification**
- Recalculables (formules vérifiées) : totaux, débits, `Down/Up Ratio`, `Packet Length Mean/Max/Min/Std/Variance`, copies exactes,
  `Flow IAT Mean`, `Fwd/Bwd IAT Mean`, compteurs PSH et RST.
- Bornes d'ordre seulement : `Flow IAT Min/Max`, `Fwd/Bwd IAT Min/Max`.
- Non recalculables : `IAT Std`, `Active*`, `Idle*`, `Bulk*`, `Subflow*`, `Total TCP Flow Time` (non modifiable).

**Limite** : les variables non recalculables seraient gardées à leur valeur d'origine lors d'une perturbation ; le réalisme est alors
seulement partiel, ce qui doit figurer dans le rapport final.