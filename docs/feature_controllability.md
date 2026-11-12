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
