"""Builds notebooks/02_final_report.ipynb (report + tables read from results/final/)."""

import json
from pathlib import Path

ANALYSIS = Path("notebooks/_analysis.md")


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n")}


cells = [
    md("""
# Attaquer son propre détecteur d'intrusion : évasion adverse et durcissement

Projet 2 du module « Machine Learning pour la cyber-sécurité » (Tek-up), réalisé **seul** : l'étudiant joue successivement le rôle du défenseur (construction et durcissement du détecteur) et de l'attaquant (évasion).

Ce notebook est le rapport. Il est exécutable de haut en bas et **ne lit que des agrégats déjà enregistrés** dans `results/final/` et des documents de `docs/` : aucune donnée brute, aucun réentraînement. Les chiffres viennent de `python -m src.evaluation.final_evaluation --segment test`, exécuté une seule fois.

Étiquettes utilisées : **Observé** (mesuré), **Hypothèse**, **Planifié**, **Post hoc** (décidé après avoir vu un résultat).
"""),
    code("""
from pathlib import Path

import pandas as pd
from IPython.display import Image, Markdown, display

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RESULTS = ROOT / "results" / "final"
DOCS = ROOT / "docs"
SEGMENT = "test"
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 200)


def load(name):
    return pd.read_csv(RESULTS / f"{SEGMENT}_{name}.csv")


def show_doc(name):
    display(Markdown((DOCS / name).read_text(encoding="utf-8")))


print(sorted(p.name for p in RESULTS.glob(f"{SEGMENT}_*")))
"""),
    md("""
## 1. Problématique

Un détecteur d'intrusion par apprentissage automatique classe des flux réseau en « normal » ou « attaque ». Un attaquant peut modifier légèrement son trafic pour être classé « normal » : c'est une **attaque d'évasion**. Questions étudiées :

1. Les détecteurs retenus (régression logistique, forêt aléatoire, XGBoost) sont-ils évadables par un attaquant réaliste ?
2. Un **entraînement adverse** les rend-il plus résistants, et à quel coût sur la performance normale ?
3. Que vaut ce résultat face à ses limites (attaquant connu, modèle de menace restreint) ?

Un résultat modeste mais honnêtement évalué vaut mieux qu'un score élevé obtenu par une évaluation biaisée.
"""),
    md("""
## 2. Données

- **CIC-IDS2017 « improved »** (CNS2022, Engelen et al.), version corrigée du jeu CIC-IDS2017 : cinq CSV journaliers (lundi à vendredi), flux réseau décrits par des statistiques (durée, paquets, octets, temps inter-arrivées…). Données publiques, aucune attaque contre un système réel.
- Archive officielle `CICIDS2017_improved.zip` (343 549 013 octets), non versionnée ; procédure d'obtention dans le README.
- Cible binaire : `BENIGN` et les variantes « Attempted » (tentatives sans effet) valent 0, les attaques effectives valent 1.

L'audit du jeu (labels, valeurs manquantes ou infinies, doublons) est dans `docs/dataset_audit_report.md`.
"""),
    md("""
## 3. Préparation des données

- 80 variables en entrée ; métadonnées, adresses IP, ports, horodatage et `Header Length` exclus (variables identifiantes qui permettraient de « tricher »).
- Toutes les opérations apprises (imputation, normalisation pour la régression logistique) sont **ajustées sur le train seulement** (`src/data/preprocessing.py`, 30 tests `unittest`).
- Détails : `docs/preprocessing_protocol.md` et `docs/preprocessing_report.md`.
"""),
    md("""
## 4. Méthodologie et découpage

**Premier protocole (par jour)** : lundi à mercredi pour le train, jeudi pour la validation, vendredi pour le test. Train et validation n'ont **aucune famille d'attaque en commun** : les modèles échouent presque totalement sur le jeudi. Ce résultat est gardé comme étude du décalage de distribution (`docs/temporal_baselines_report.md`).

**Protocole retenu (par strate), post hoc** : lundi à mercredi seulement ; chaque couple (jour, label) est trié par temps et coupé à 60 / 20 / 20 avec un intervalle d'exclusion de 1 % autour de chaque coupure (`src/data/temporal_split.py`). Train 702 310 lignes, validation 214 261, test 226 157. Ce choix a été fait **après** avoir vu les résultats du jeudi : le résultat principal est donc une **borne optimiste** (mêmes familles d'attaque en train et en test).

**Discipline d'évaluation** : réglage et développement sur la validation uniquement ; spécifications commitées **avant** exécution (`docs/hardening_specification.md`, `docs/final_evaluation_specification.md`) ; le segment test est lu **une seule fois**, par un script qui vérifie d'abord que les six modèles reconstruits reproduisent exactement les FP/FN de la validation.
"""),
    code("""
check = load("validation_check")
display(check)
print("Reproduction des modèles :", "OK" if check["match"].all() else "ÉCART")
"""),
    md("""
## 5. Modèle de menace

Résumé (détail dans les documents ci-dessous) : attaquant **boîte noire à score** (il interroge le détecteur et lit sa probabilité), **1 000 requêtes au plus par flux**, qui ne perturbe que des attaques **déjà détectées** (sinon l'évasion serait gratuite). Il ne contrôle que le côté `Fwd` du flux (**hypothèse** non prouvée : l'attaquant est le client qui initie la connexion) : remplissage des paquets (facteur `s`) et délai (facteur `t`), tous deux dans `[1, 1 + A]`. Les variables dérivées sont recalculées par des formules **vérifiées sur les données** ; une règle de réalisme rejette tout candidat hors des bornes du train, qui casse un ordre vérifié ou dépasse 1 500 octets par paquet.
"""),
    code("""
show_doc("threat_model.md")
"""),
    code("""
show_doc("feature_controllability.md")
"""),
    md("""
## 6. Modèles

Configurations retenues par une règle de réglage **déclarée avant exécution** (graine 42, seuil 0,5, `docs/tuning_report.md`) :

| Modèle | Configuration |
|---|---|
| Régression logistique (baseline) | `C = 0,1`, variables normalisées |
| Forêt aléatoire | 100 arbres, `min_samples_leaf = 20` |
| XGBoost | profondeur 3, 100 arbres |

Défaut reconnu : la tolérance de 0,001 de la règle de sélection est plus grande que l'écart de PR-AUC entre configurations de la forêt et de XGBoost ; elle a donc choisi par simplicité.
"""),
    md("""
## 7. Attaque d'évasion

- **Recherche aléatoire** : pour chaque flux, des couples `(s, t)` tirés uniformément dans `[1, 1 + A]²`, candidats irréalistes rejetés sans requête, au plus 1 000 requêtes ; amplitudes A = 0,1 ; 0,25 ; 0,5 ; 1 ; 2 (graine 1234).
- **Grille déterministe** 31 × 31 sur `[1, 3]²` (A = 2, 961 requêtes au plus) pour vérifier que la recherche aléatoire ne rate pas des évasions.
- **Population d'évasion** : au plus 300 flux détectés par famille et par modèle (graine 42). **Population commune** : au plus 300 attaques par famille, identiques pour les six modèles ; un flux manqué au départ ou évadé compte comme manqué (rappel sous attaque).

Résultat de développement (validation, `docs/multi_target_attack_report.md`) : XGBoost quasi insensible (2 évasions sur 1 800 flux), car l'essentiel de son importance porte sur des variables `Bwd` que l'attaquant ne contrôle pas. **Post hoc** : la régression logistique et la forêt sont attaquables (SSH-Patator surtout).
"""),
    md("""
## 8. Défense : entraînement adverse

Spécification commitée avant le code (`docs/hardening_specification.md`) : pour chaque flux d'attaque du **train**, une copie perturbée réalisable (20 tirages dans `[1, 2]²`, premier candidat réalisable, A_train = 1), ajoutée à l'entraînement avec l'étiquette 1 ; réentraînement depuis zéro, mêmes hyperparamètres. Sur le train : 105 045 copies ajoutées, 319 flux sans candidat réalisable, part d'attaques de 15,00 % à 26,06 %. L'évaluation utilise une **autre graine**, une autre méthode (grille) et une **force supérieure** (A = 2 > A_train).
"""),
    md("""
## 9. Résultats (segment test, exécution unique)

### 9.1 Performance propre
"""),
    code("""
clean = load("clean")
display(clean.round(4))
"""),
    code("""
display(load("per_class").round(4))
"""),
    code("""
display(Image(filename=str(RESULTS / f"{SEGMENT}_pr_curves.png")))
"""),
    code("""
fam = load("per_family_clean")
display(fam.pivot_table(index=["family", "n"], columns=["detector", "state"], values="recall").round(4))
"""),
    md("""
### 9.2 Rappel sous attaque selon l'amplitude, avant et après durcissement
"""),
    code("""
display(Image(filename=str(RESULTS / f"{SEGMENT}_recall_vs_amplitude.png")))
pooled = load("recall_common_pooled")
display(pooled.pivot_table(index=["detector", "state"], columns="attack", values="recall").round(4))
"""),
    md("""
### 9.3 Taux d'évasion et nombre de requêtes
"""),
    code("""
evasion = load("evasion")
informative = evasion[evasion["evaded"] > 0]
cols = ["detector", "state", "family", "attack", "attacked", "evaded", "rate", "ci_low", "ci_high",
        "median_queries_evaders", "max_queries_evaders"]
display(informative[cols].round(4))
comparison = load("evasion_comparison")
print(comparison["verdict"].value_counts())
"""),
    md("""
### 9.4 Coût du durcissement sur des flux normaux perturbés
"""),
    code("""
display(load("benign_perturbed").round(4))
"""),
    md("""
### 9.5 Vendredi : étude du décalage (exécution unique, séparée)

Le vendredi (Portscan, DDoS, Botnet) contient des **familles absentes du train** : il mesure la généralisation hors distribution, pas la robustesse adverse. **Post hoc** : une première exécution s'est arrêtée sur un label inconnu (`Botnet - Attempted`, propre au vendredi) **avant tout calcul de score** ; il a été ajouté aux labels « Attempted » (valeur 0) par un commit séparé, puis l'évaluation a été relancée.
"""),
    code("""
FRIDAY = RESULTS / "friday_clean.csv"
if FRIDAY.exists():
    display(pd.read_csv(FRIDAY).round(4))
    fri = pd.read_csv(RESULTS / "friday_per_family_clean.csv")
    display(fri.pivot_table(index=["family", "n"], columns=["detector", "state"], values="recall").round(4))
    fpool = pd.read_csv(RESULTS / "friday_recall_common_pooled.csv")
    display(fpool.pivot_table(index=["detector", "state"], columns="attack", values="recall").round(4))
    display(Image(filename=str(RESULTS / "friday_recall_vs_amplitude.png")))
else:
    print("Vendredi non évalué.")
"""),
    md("__ANALYSIS__"),
]

analysis = ANALYSIS.read_text(encoding="utf-8") if ANALYSIS.exists() else "## 10. Analyse critique\n\nÀ compléter."
cells[-1] = md(analysis)

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for i, cell in enumerate(notebook["cells"]):
    cell["id"] = f"cell-{i:02d}"
Path("notebooks/02_final_report.ipynb").write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8"
)
print("written: notebooks/02_final_report.ipynb")