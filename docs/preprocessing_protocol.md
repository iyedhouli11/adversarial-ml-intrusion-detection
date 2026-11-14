# Leakage-Safe Preprocessing Protocol

**Statut : implémentation initiale ; aucun modèle n'a encore été entraîné.**

## Objectif

Préparer les données CNS2022 pour la classification supervisée sans modifier
les CSV bruts et sans utiliser le vendredi pendant le développement.

## Target binaire

La fonction `target_from_labels` conserve la colonne `Label` originale et
produit une série séparée :

```text
BENIGN          -> Normal = 0
X - Attempted   -> Normal = 0
Effective attack -> Attack = 1
```

Les labels inconnus déclenchent une erreur explicite. `Attempted Category` et
`attempted_flag` sont des métadonnées d'audit et ne peuvent pas entrer dans
`X`.

## Nettoyage de la copie de travail

- `+inf` et `-inf` sont remplacés par `NaN` uniquement dans une copie de travail.
- Les valeurs négatives de `Fwd Header Length` et `Bwd Header Length` ne sont
  pas écrasées dans les données brutes.
- Stratégie A (`header_strategy="impute"`) : valeurs négatives converties en
  `NaN`, puis imputation médiane ajustée sur l'entraînement.
- Stratégie B (`header_strategy="exclude"`) : les deux colonnes sont exclues de
  `X`, sans modifier la copie source.
- Les zéros et les autres valeurs extrêmes ne sont pas supprimés
  automatiquement.

La comparaison prédictive entre A et B sera réalisée avec la baseline et la
validation du jeudi. À ce stade, le pipeline implémente les deux stratégies
mais aucun modèle n'est entraîné.

## Features et métadonnées

Sont exclus de l'entrée initiale du modèle :

```text
id, Flow ID, Src IP, Dst IP, Timestamp, Label,
Attempted Category, source_day
```

Les ports source et destination sont également exclus par défaut afin de
réduire les artefacts spécifiques au laboratoire. Une analyse de sensibilité
pourra les réintroduire. `Protocol` est traité comme une variable catégorielle,
pas comme une grandeur continue.

Cette décision de feature inclusion est indépendante de la contrôlabilité de
l'attaquant. Une variable non modifiable peut rester utile au détecteur.

## Pipeline

`ColumnTransformer` combine :

- une pipeline numérique avec imputation médiane et, pour les modèles qui le
  nécessitent, `StandardScaler` ;
- une pipeline catégorielle avec imputation par mode et
  `OneHotEncoder(handle_unknown="ignore")`.

`fit` apprend les statistiques uniquement sur l'entraînement. `transform`
réutilise ces statistiques sur validation et test. `fit_transform` n'est
autorisé que sur l'entraînement.

## Découpage

```text
Training   : monday.csv + tuesday.csv + wednesday.csv
Validation : thursday.csv
Test       : friday.csv
```

Le découpage est par jour et non par lignes aléatoires. Il mesure une
combinaison de changement de distribution entre jours et de changement de
familles d'attaques. Le test du vendredi reste isolé jusqu'à l'évaluation
finale.

## Mémoire et reproductibilité

L'audit a mesuré environ 102 MiB par chunk de 100 000 lignes et environ
16,91 Go de RAM libre au démarrage de cette phase. Le loader lit les fichiers
journaliers séquentiellement au lieu de charger les cinq fichiers ensemble.

Versions runtime vérifiées :

```text
Python 3.11.0
numpy 2.4.6
pandas 3.1.1
scikit-learn 1.8.0
```
