# Adversarial Machine Learning for Network Intrusion Detection

Projet académique de cybersécurité consacré à l'évasion adverse contre un système de détection d'intrusion basé sur l'apprentissage automatique.

## Objectif

Le projet adopte deux perspectives :

- **Blue Team** : construire, évaluer et durcir un détecteur de trafic normal et malveillant ;
- **Red Team** : rechercher des modifications contraintes permettant à un trafic malveillant correctement détecté d'être classé comme normal.

Les expériences seront hors ligne, reproductibles et réalisées uniquement sur des données publiques. Aucune attaque ne sera lancée contre un système réel.

## État actuel

- Dépôt Git local indépendant initialisé sur la branche `main` ;
- CNS2022 `CICIDS2017_improved.zip` sélectionné et vérifié ;
- cinq CSV journaliers extraits dans `data/raw/CICIDS2017_improved/` ;
- audit metadata-only exécuté et rapport généré ;
- aucun modèle entraîné et aucun résultat de classification produit ;
- le découpage lundi-mercredi / jeudi / vendredi reste provisoire.

## Structure prévue

```text
docs/       protocole, dataset, contrôlabilité, menace et rapport
src/        logique réutilisable de données, modèles, attaques et évaluation
notebooks/  exploration et expériences reproductibles
tests/      tests des contraintes et des fonctions principales
results/    figures et résumés sélectionnés, jamais les données brutes
requirements.txt      dépendances runtime minimales
requirements-dev.txt  dépendances optionnelles pour Jupyter
```

Les données brutes, intermédiaires et traitées sont exclues par `.gitignore`.

## Méthodologie prévue

La comparaison comprendra une régression logistique, une forêt aléatoire et XGBoost. Les métriques principales seront la matrice de confusion, précision, rappel, F1-score, PR-AUC, temps d'entraînement et temps d'inférence. Les opérations apprises seront ajustées sur l'entraînement uniquement et le test final ne sera utilisé qu'une fois.

L'attaque initiale sera une recherche aléatoire de perturbations bornées dans l'espace des caractéristiques, avec un budget maximal de 1 000 requêtes par échantillon. Une modification de ligne CSV ne sera pas présentée comme une modification de paquets réseau sans reconstruction et vérification supplémentaires.

## Phase 3 — audit initial du dataset

Dataset : [CIC-IDS2017 Improved — CNS2022](https://intrusion-detection.distrinet-research.be/CNS2022/CICIDS2017.html).
L'archive officielle est `CICIDS2017_improved.zip`. Les cinq CSV sont extraits
dans `data/raw/CICIDS2017_improved/`. Les données brutes sont ignorées par Git
et ne doivent jamais être commit ou poussées.

### Installation runtime

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Audit reproductible

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m src.data.audit_dataset
```

Le rapport agrégé est généré dans
`docs/dataset_audit_report.md`. Il ne contient pas d'échantillons bruts. Les
résultats actuels décrivent les cinq jours, les labels, le schéma, les valeurs
manquantes ou infinies, les doublons candidats et la faisabilité du split.

### Acquisition et extraction

L'archive officielle est disponible à :

```text
https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip
```

La taille vérifiée est `343549013` octets. L'extraction doit produire
`monday.csv`, `tuesday.csv`, `wednesday.csv`, `thursday.csv` et `friday.csv`
dans `data/raw/CICIDS2017_improved/`. L'archive, les CSV bruts et les données
traitées restent hors Git.

### Notebook

Le notebook peut être lu et ses cellules ont été validées séquentiellement avec
le `.venv`. L'exécution native par Jupyter n'est pas encore installée dans
l'environnement runtime. Après approbation séparée, les dépendances de
développement prévues sont :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks\01_dataset_audit.ipynb
```

Les outputs du notebook doivent rester agrégés et ne jamais contenir de lignes
brutes du dataset.

## Reproductibilité

L'environnement cible est Python 3.11 dans un environnement virtuel local. Les versions, graines aléatoires, configurations, procédures d'acquisition et limites connues seront documentées avant les expériences. Les résultats publiés devront être mesurés ; aucune valeur ne sera inventée.

## Organisation individuelle

Le projet est réalisé intégralement par un seul étudiant. La progression suit les dépendances scientifiques : audit du dataset, pipeline reproductible, modèles, menace, attaque, durcissement, évaluation finale, rapport et présentation.

La branche `main` suffit pour le travail initial. Une branche temporaire ne sera utilisée que si une modification isolée apporte un avantage réel. Chaque étape sera validée avant de commencer la suivante et chaque commit représentera une contribution réellement effectuée.

## Références initiales

- [CIC-IDS2017 — Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html)
- [UNSW-NB15 — UNSW Research](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
- [CICIDS2017 quality analysis — HAL](https://hal.science/hal-03775466)
