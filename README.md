# Adversarial Machine Learning for Network Intrusion Detection

Projet académique de cybersécurité consacré à l'évasion adverse contre un système de détection d'intrusion basé sur l'apprentissage automatique.

## Objectif

Le projet adopte deux perspectives :

- **Blue Team** : construire, évaluer et durcir un détecteur de trafic normal et malveillant ;
- **Red Team** : rechercher des modifications contraintes permettant à un trafic malveillant correctement détecté d'être classé comme normal.

Les expériences seront hors ligne, reproductibles et réalisées uniquement sur des données publiques. Aucune attaque ne sera lancée contre un système réel.

## État actuel

- Dépôt Git local indépendant initialisé sur la branche `main` ;
- CIC-IDS2017 retenu comme candidat provisoire ;
- protocole de baseline et d'évaluation préparé ;
- modèle de menace et audit de contrôlabilité en préparation ;
- aucune donnée téléchargée ;
- aucun modèle entraîné et aucun résultat expérimental produit.

Le découpage lundi-mercredi / jeudi / vendredi reste provisoire jusqu'à l'inspection des métadonnées et à l'audit du nombre d'échantillons malveillants correctement détectés.

## Structure prévue

```text
docs/       protocole, dataset, contrôlabilité, menace et rapport
src/        logique réutilisable de données, modèles, attaques et évaluation
notebooks/  exploration et expériences reproductibles
tests/      tests des contraintes et des fonctions principales
results/    figures et résumés sélectionnés, jamais les données brutes
```

Les données brutes, intermédiaires et traitées sont exclues par `.gitignore`.

## Méthodologie prévue

La comparaison comprendra une régression logistique, une forêt aléatoire et XGBoost. Les métriques principales seront la matrice de confusion, précision, rappel, F1-score, PR-AUC, temps d'entraînement et temps d'inférence. Les opérations apprises seront ajustées sur l'entraînement uniquement et le test final ne sera utilisé qu'une fois.

L'attaque initiale sera une recherche aléatoire de perturbations bornées dans l'espace des caractéristiques, avec un budget maximal de 1 000 requêtes par échantillon. Une modification de ligne CSV ne sera pas présentée comme une modification de paquets réseau sans reconstruction et vérification supplémentaires.

## Reproductibilité

L'environnement cible est Python 3.11 dans un environnement virtuel local. Les versions, graines aléatoires, configurations, procédures d'acquisition et limites connues seront documentées avant les expériences. Les résultats publiés devront être mesurés ; aucune valeur ne sera inventée.

## Organisation individuelle

Le projet est réalisé intégralement par un seul étudiant. La progression suit les dépendances scientifiques : audit du dataset, pipeline reproductible, modèles, menace, attaque, durcissement, évaluation finale, rapport et présentation.

La branche `main` suffit pour le travail initial. Une branche temporaire ne sera utilisée que si une modification isolée apporte un avantage réel. Chaque étape sera validée avant de commencer la suivante et chaque commit représentera une contribution réellement effectuée.

## Références initiales

- [CIC-IDS2017 — Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html)
- [UNSW-NB15 — UNSW Research](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
- [CICIDS2017 quality analysis — HAL](https://hal.science/hal-03775466)
