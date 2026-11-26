# Adversarial ML Intrusion Detection (évasion adverse et durcissement)

Projet 2 du module « Machine Learning pour la cyber-sécurité » (Tek-up), réalisé **seul** : l'étudiant joue successivement le rôle du défenseur (détecteur, durcissement) et de l'attaquant (évasion). Données publiques uniquement, aucune attaque contre un système réel.

**Le rapport est le notebook [`notebooks/02_final_report.ipynb`](notebooks/02_final_report.ipynb)** (12 sections : problématique, données, préparation, méthodologie, modèle de menace, modèles, attaque, défense, résultats, analyse critique, limites, conclusion). Il lit les agrégats enregistrés dans `results/final/` et s'exécute de haut en bas en quelques secondes.

## Résultats principaux (segment test, exécution unique)

Rappel sur la population commune (au plus 300 attaques par famille), propre puis sous l'attaque par grille (amplitude A = 2) :

| Détecteur | Original | Durci (entraînement adverse) |
|---|---|---|
| Régression logistique | 0,818 → 0,490 | 0,832 → 0,813 |
| Forêt aléatoire | 0,836 → 0,675 | 0,845 → 0,844 |
| XGBoost | 0,919 → 0,866 | 0,927 → 0,926 |

- Performance propre sur 226 157 flux : F1 de 0,987 (régression logistique) à 0,996 (XGBoost). C'est une **borne optimiste** (mêmes familles d'attaque en train et en test).
- Les trois détecteurs sont évadables par un attaquant boîte noire qui ne fait que remplir ses paquets et retarder son trafic côté client. Le durcissement ramène le rappel presque au niveau propre, **contre l'attaque connue seulement**.
- **Vendredi (familles inconnues : Portscan, DDoS, Botnet)** : rappel propre de 0,27 à 0,69 seulement, et XGBoost durci reste évadé à 98,7 % sur DDoS. Le score du découpage par strate ne se généralise pas aux attaques nouvelles.
- Courbes exigées : `results/final/test_recall_vs_amplitude.png` (rappel selon l'amplitude, avant et après durcissement) et `results/final/test_pr_curves.png`.

## Structure

```text
docs/        protocoles, spécifications commitées avant exécution, rapports par expérience
src/data/    chargement, audit, prétraitement sans fuite, découpage temporel par strate
src/models/  baselines, réglage sur la validation, profils des détecteurs
src/attacks/ couche de perturbation réaliste, recherche aléatoire, grille, attaque multi-détecteurs
src/defenses/ entraînement adverse, contrôle des flux normaux perturbés
src/evaluation/ évaluation finale unique et figures
notebooks/   01 audit du jeu, 02 rapport final
results/final/ agrégats CSV, figures et sortie console de l'évaluation finale (aucune donnée brute)
tests/       30 tests unittest
```

## Installation

Python 3.11, Windows PowerShell (les commandes sont équivalentes ailleurs).

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt   # ruff, jupyter, ipykernel (notebook)
```

Versions épinglées dans `requirements.txt` (numpy 2.4.6, pandas 3.1.1, scikit-learn 1.8.0, scipy 1.17.1, xgboost 3.2.0, matplotlib 3.11.2).

## Données (non versionnées)

Jeu : [CIC-IDS2017 Improved, CNS2022](https://intrusion-detection.distrinet-research.be/CNS2022/CICIDS2017.html). Télécharger l'archive officielle :

```text
https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip
```

Taille vérifiée : `343549013` octets. L'extraction doit produire `monday.csv` … `friday.csv` dans `data/raw/CICIDS2017_improved/`. L'archive, les CSV et toute donnée traitée sont ignorés par Git.

## Reproduction

```powershell
python -m unittest discover -s tests          # 30 tests
python -m ruff check src tests
python -m src.data.audit_dataset              # audit du jeu
python -m src.defenses.adversarial_training   # durcissement, validation seulement
python -m src.evaluation.final_evaluation --segment test     # une seule fois (environ 15 min)
python -m src.evaluation.final_evaluation --segment friday   # une seule fois, après le test
python -m src.evaluation.make_figures --segment test
python -m jupyter nbconvert --to notebook --execute --inplace notebooks\02_final_report.ipynb
```

`final_evaluation` reconstruit les six modèles, vérifie d'abord qu'ils reproduisent exactement les FP/FN de la validation, puis refuse de s'exécuter deux fois sur le même segment (supprimer `results/final/<segment>_clean.csv` pour un essai de reproduction).

Graines fixées : 42 (modèles, populations, copies adverses), 1234 (attaque d'évaluation), 99 (contrôle des flux normaux).

## Rigueur et provenance

- Le test et le vendredi ne servent qu'à l'évaluation finale ; tout le réglage est fait sur la validation.
- Spécifications commitées avant exécution : `docs/hardening_specification.md`, `docs/final_evaluation_specification.md`.
- Déclaré honnêtement : le découpage par strate a été choisi après les résultats du jeudi (post hoc) ; la spécification d'attaque v1 a été enregistrée rétroactivement ; l'attaque de la régression logistique et de la forêt et le durcissement des trois modèles sont post hoc. Liste complète : `docs/PROJECT_HANDOFF.md`, section 10.

## Limites

Attaquant non adaptatif (évalué contre l'attaque connue) ; deux perturbations seulement (remplissage et délai côté `Fwd`) ; modification de lignes de flux, pas de paquets réels ; une seule graine d'entraînement ; borne optimiste du découpage par strate.
