# Modeling Protocol — Individual Work

**Statut : préparation documentaire uniquement. Aucun modèle n'a encore été entraîné.**

## Objectif

Définir un pipeline reproductible pour comparer une baseline, une forêt aléatoire et XGBoost, sans fuite d'information et sans confondre les variables utilisées par le détecteur avec les variables modifiables par l'attaquant.

## Contrat de données proposé

Chaque ligne devra conserver, séparément des entrées du modèle :

- `sample_id` : identifiant interne stable ;
- `capture_day` : jour de capture ou groupe temporel ;
- `attack_family` : famille originale, utilisée pour l'analyse ;
- `label` : `0` pour normal et `1` pour attaque ;
- `features` : variables candidates du détecteur.

`sample_id`, `capture_day`, `attack_family` et `label` ne doivent pas entrer automatiquement dans le modèle. Leur inclusion éventuelle devra être justifiée par un audit de fuite ou d'artefact.

## Découpage provisoire

Le protocole de travail proposé est :

- entraînement : lundi, mardi et mercredi ;
- validation : jeudi ;
- test final : vendredi.

Ce découpage reste bloqué jusqu'à l'audit des métadonnées. L'audit doit compter les attaques par jour et par famille, puis compter les attaques correctement détectées par le modèle initial. L'évasion ne sera développée que si la validation possède un nombre suffisant de cas exploitables. Si nécessaire, un sous-ensemble d'attaque sera séparé par session ou période, jamais par lignes aléatoires corrélées.

## Prétraitement

Le pipeline devra :

1. identifier les doublons, valeurs manquantes et valeurs infinies ;
2. appliquer les règles de nettoyage sans modifier les données brutes ;
3. séparer les colonnes numériques et catégorielles après l'audit ;
4. ajuster imputation, encodage, standardisation, sélection et rééquilibrage sur l'entraînement seulement ;
5. conserver le même schéma de colonnes pour validation, test et attaques.

La contrôlabilité est une propriété de l'attaquant, pas une règle automatique d'exclusion du détecteur. Une variable non modifiable peut rester utile au détecteur si elle est observable et non fuyante.

## Modèles et réglage

La baseline prévue est une régression logistique avec préparation adaptée aux variables retenues. Elle sera comparée à une forêt aléatoire et à XGBoost. Les hyperparamètres seront fixés avec l'entraînement et la validation uniquement. Les configurations, graines et versions devront être enregistrées avec chaque expérience.

## Évaluation

Pour chaque modèle, enregistrer :

- matrice de confusion ;
- précision, rappel et F1-score par classe ;
- PR-AUC ;
- temps d'entraînement et d'inférence ;
- seuil de décision utilisé.

Le test final sera exécuté après gel du pipeline, du modèle, du seuil et du protocole d'attaque. Aucune sélection ne sera faite à partir de ses résultats.

## Critères d'acceptation

- aucune transformation ajustée sur le test ;
- schéma stable entre les trois périodes ;
- métriques reproductibles avec une graine fixée ;
- audit de faisabilité des attaques terminé avant l'utilisation du test ;
- absence de résultat présenté avant exécution réelle.

## Organisation du travail

L'auteur réalise séquentiellement l'audit des données, le pipeline, les modèles et l'évaluation. La branche `main` est suffisante au départ ; une branche temporaire ne sera créée que si elle réduit un risque réel. Aucun résultat ou commit ne sera attribué à une autre personne.
