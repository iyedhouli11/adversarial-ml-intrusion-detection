# PROJECT_HANDOFF : Attaquer son propre détecteur (évasion adverse contre un IDS par machine learning)

Fichier de passation pour une nouvelle conversation avec une IA. Rédigé le 23 novembre 2026 à partir de la conversation précédente.
Tout chiffre ci-dessous a été mesuré par l'étudiant sur sa machine et collé dans la conversation. L'IA n'exécute aucun code : l'étudiant lance les commandes PowerShell et colle les sorties.

## 0. Message de démarrage à coller avec ce fichier

> Voici le fichier de passation de mon projet. Reprends le rôle décrit en section 1. Avant toute chose, demande-moi de coller la sortie de
> `git status -sb` et `git log --oneline -20` pour vérifier l'état réel du dépôt, puis dis-moi ce que tu comprends de l'état actuel et la prochaine étape. Ne relance aucune expérience déjà faite.

## 1. Rôle de l'IA et règles de travail (à respecter strictement)

- Rôle : professeur de machine learning, ingénieur cybersécurité et mentor Git/GitHub pour un étudiant **qui travaille seul** (le cahier des charges parle d'un binôme ; ignorer les consignes de collaboration à deux).
- Langue : français (termes académiques), l'étudiant écrit parfois en arabe tunisien latinisé ; répondre en français simple, on peut expliquer un point difficile en tunisien.
- **L'IA ne peut pas exécuter de code.** Toute création de fichier se fait **par commande PowerShell** (here-string `@' ... '@` puis `[System.IO.File]::WriteAllText(..., UTF8 sans BOM)`). L'étudiant a explicitement demandé : « create with commands always ».
- Pour modifier un fichier existant : fonction `Replace-Once` qui s'arrête (`throw`) si le bloc cherché n'apparaît pas exactement une fois.
- Attendre la sortie de l'étudiant avant de continuer. Si une erreur apparaît : diagnostiquer avec l'erreur réelle, ne pas corriger à l'aveugle.
- Git : jamais `git add .` ; toujours `git status --short --untracked-files=all` et `git diff --check` avant ; fichiers ajoutés un par un ; **aucun commit ni push sans l'approbation de l'étudiant** ; vérifier la sortie du push (`ancien..nouveau  main -> main`) avant de dire « publié ». Jamais de données brutes, de secrets ni de force push.
- Rigueur scientifique : aucun chiffre inventé ; étiqueter **Observé / Hypothèse / Planifié / Post hoc** ; déclarer les protocoles **et les commiter avant** d'exécuter ; ne jamais utiliser le segment test ni le vendredi pendant le développement ; un score très élevé est une borne optimiste, pas une preuve.
- Pédagogie : expliquer chaque concept simplement. **Les questions de compréhension ne se posent qu'à la fin du projet** (demande de l'étudiant) ; la liste est en section 12.
- Ne pas mentionner de date limite inventée : la date de la dernière séance est dans le calendrier du semestre Tek-up ; **elle est inconnue** et doit être demandée.

## 2. Cadre académique

Module « Machine Learning pour la cyber-sécurité » (Tek-up). **Projet 2 : Attaquer son propre détecteur.** Données publiques uniquement, aucune attaque contre un système réel.

Socle commun exigé : baseline (régression logistique ou arbre), forêt aléatoire, XGBoost avec réglage par validation croisée ou jeu de validation ; découpage train/validation/test sans fuite (test utilisé une seule fois) ; matrice de confusion, précision, rappel, F1, PR-AUC, discussion du coût FP/FN, temps d'entraînement et d'inférence ; l'accuracy seule est refusée.

Exigences propres au projet 2 : modèle de menace explicite ; tableau à 3 catégories (librement modifiable / modifiable avec un coût / non modifiable) ; au moins une attaque d'évasion respectant le modèle (budget 1 000 requêtes par échantillon) ; taux d'évasion, chute du rappel selon l'amplitude, nombre de requêtes ; vérification du réalisme ; durcissement (entraînement adverse ou règles) avec effet sur la performance normale ; ré-attaque du modèle durci ; courbes de rappel selon l'amplitude avant et après durcissement ; discussion honnête des limites.

Livrables : notebook reproductible exécutable de haut en bas **contenant le rapport** (problématique, données, méthodes, résultats, analyse critique, limites) ; dépôt Git (README, graines, versions, instructions d'obtention des données, pas de données brutes) ; présentation orale avec questions individuelles.
Grille : rigueur de l'évaluation 30 %, qualité des modèles et comparaison 20 %, approfondissement et analyse critique 30 %, reproductibilité et clarté 10 %, présentation 10 %.
Jalons : 13 novembre (page baseline et protocole, déjà passé) ; rendu final = dernière séance du cours (date inconnue).

## 3. Environnement et dépôt

- Windows, PowerShell, Python 3.11.0, venv `.venv`. Versions épinglées : numpy 2.4.6, pandas 3.1.1, scikit-learn 1.8.0, scipy 1.17.1, xgboost 3.2.0 ; outil de développement : ruff 0.17.5 (`requirements-dev.txt` contient aussi jupyter 1.1.1 et ipykernel 7.4.0, **non installés** : installation à approuver séparément).
- GitHub : https://github.com/iyedhouli11/adversarial-ml-intrusion-detection (branche `main`).
- Données : CIC-IDS2017 « improved » (CNS2022), archive officielle `CICIDS2017_improved.zip` (343 549 013 octets), cinq CSV `monday.csv` … `friday.csv` dans `data/raw/CICIDS2017_improved/` (ignorés par Git), encodage cp1252.
- Structure : `docs/` (protocoles, rapports, `threat_model.md`, `feature_controllability.md`, `attack_specification.md`, `hardening_specification.md`, rapports par expérience), `src/data/` (audit, loader, prétraitement, découpage temporel, inventaires), `src/models/` (baselines, réglage, sensibilité, profil du détecteur), `src/attacks/` (perturbation, attaque, grille, multi-détecteurs), `src/defenses/` (entraînement adverse, contrôle), `tests/` (30 tests `unittest`), `notebooks/` (vide pour l'instant), `results/` (vide pour l'instant).

Historique Git observé (ordre chronologique) :

| Commit | Contenu |
|---|---|
| 02b2eaa | initialisation du projet |
| a328b3f | audit reproductible du dataset (Phase 3) |
| a54e591 | prétraitement sans fuite (Phase 4.1) |
| caee95c | régression logistique + diagnostic de seuil |
| 3a6fbe8 | forêt aléatoire sur le découpage par jour |
| f2879e3 | découpage temporel par strate |
| 2796618 | régression logistique et forêt sur ce découpage |
| 5447376 | XGBoost + `xgboost==3.2.0` |
| 40683bf | sensibilité de l'intervalle et des doublons |
| 237690b | test « une famille retirée » |
| ea9aaa3 | réglage des hyperparamètres |
| 3bc7c16, e2c21fe | inventaire et relations des variables (même message de commit, sans gravité) |
| 32c1a8e | profil du détecteur + spécification d'attaque provisoire |
| 8a7261c | couche de perturbation |
| fc49df7 | faisabilité par famille |
| ba37b82 | attaque par recherche aléatoire + premiers résultats |
| 01d297a | **inconnu** : vu seulement comme parent de 31c2cce ; à identifier |
| 31c2cce | spécification du durcissement (commitée **avant** tout script de durcissement) |

**Publication non vérifiée** (l'étudiant n'a pas collé la sortie du push) : `src/attacks/grid_check.py` + `docs/grid_check_report.md` ; `src/attacks/multi_target_attack.py` + `docs/multi_target_attack_report.md` ; commit rétroactif de la spécification v1 (`docs/attack_specification.md`, `docs/perturbation_feasibility_report.md`, `src/attacks/reachable_gain.py`) ; `src/defenses/*` + `docs/hardening_report.md` avec l'addendum du contrôle post hoc. Vérifier avec `git status -sb` et `git log --oneline -20` ; des scripts de commit de l'IA s'arrêtent d'eux-mêmes si un fichier précédent n'est pas suivi par Git.

## 4. Données et prétraitement (Phases 3 et 4.1)

- Cible binaire : `BENIGN` et toutes les variantes `- Attempted` → 0 ; attaque effective → 1 ; label inconnu → erreur. `Attempted Category`, `attempted_flag`, `source_day` restent hors de X.
- Exclus du modèle (12 colonnes) : `id`, `Flow ID`, `Src IP`, `Dst IP`, `Src Port`, `Dst Port`, `Timestamp`, `Fwd/Bwd Header Length` (stratégie `exclude`), `Label`, `Attempted Category`, `source_day`. 80 variables en entrée (79 numériques + `Protocol` catégorielle), 83 colonnes après one-hot (4 valeurs de `Protocol`).
- `+inf/-inf` → NaN sur copie de travail ; imputation médiane ; `StandardScaler` seulement pour la régression logistique ; tout est ajusté sur le train uniquement (`ColumnTransformer`).
- Anomalies : 309 valeurs négatives de `Fwd Header Length` et 472 de `Bwd` (débordement int16 **non confirmé**) ; `Total TCP Flow Time` > `Flow Duration` dans 4,37 % des lignes d'entraînement (TCP uniquement, cause non expliquée) ; trois colonnes URG constantes à 0 ; `ICMP Type/Code` sont des identifiants, pas des mesures.

## 5. Protocoles de découpage

1. **Par jour (protocole d'origine)** : train lundi+mardi+mercredi (1 190 343 lignes, 15,00 % d'attaques), validation jeudi (362 076, 99,8 % des attaques sont `Infiltration - Portscan`), test vendredi. Train et validation **ne partagent aucune famille d'attaque**. Résultat observé : régression logistique (B) rappel 0,0786 et PR-AUC 0,6091 ; forêt 0 attaque détectée à 0,5 et PR-AUC 0,4156 ; conservé comme étude du décalage de distribution.
2. **Par strate (protocole de développement actuel)** : lundi à mercredi uniquement, chaque strate (jour × label) ordonnée par temps, coupée à 60 % / 20 % / 20 % avec intervalle de 1 % (`src/data/temporal_split.py`). Observé : train 702 310, validation 214 261, **test 226 157 (jamais utilisé)**, gap 47 615 ; part d'attaques 0,15 partout. Raison : un découpage 80/20 par jour est inutilisable (les attaques sont dans des fenêtres étroites ; les 20 % finaux contiennent 12 attaques sur environ 238 000 flux).
   Limite : borne optimiste. Le choix a été fait après avoir vu les résultats du jeudi (validation). Le vendredi et le segment test restent isolés.

## 6. Modèles (Phase 4)

Sur le découpage par strate, validation, seuil 0,5 (hyperparamètres par défaut, une graine) : régression logistique F1 0,9888 / PR-AUC 0,9969 ; forêt F1 0,9998 / PR-AUC 1,0 ; XGBoost F1 0,9991 / PR-AUC 1,0. Sensibilité (intervalle 1 % ou 5 %, doublons exacts supprimés ou non : 82 453 lignes retirées, 6,9 %) : écarts de F1 ≤ 0,0024. Test « une famille retirée » : les deux Patator ne sont jamais détectés quand elles sont absentes de l'entraînement ; les DoS partiellement.

**Réglage sur la validation (règle déclarée avant exécution)** : meilleure PR-AUC ; configurations à moins de 0,001 de la meilleure = ex æquo, on garde la plus simple. Retenus : régression logistique `C=0,1` (509 FP / 274 FN, PR-AUC 0,996517) ; forêt 100 arbres `min_samples_leaf=20` (11 FP / 40 FN) ; XGBoost profondeur 3, 100 arbres, `learning_rate=0,1` (7 FP / 36 FN). **Défaut de conception reconnu** : la tolérance de 0,001 est plus grande que l'écart de PR-AUC entre configurations de la forêt et de XGBoost, donc la règle y a choisi par simplicité. Une lecture secondaire (minimiser les FN à PR-AUC égale) est rapportée comme post hoc. Graine 42 partout ; seuil 0,5 figé.

## 7. Modèle de menace et perturbation (Phase 5)

- Attaquant boîte noire à score, 1 000 requêtes au plus par flux, ne perturbe que les attaques **déjà détectées à 0,5** (les flux `Attempted` et les attaques déjà manquées sont exclus du dénominateur).
- Hypothèse de travail (non prouvée) : l'attaquant est le client qui initie le flux, `Fwd` = attaquant, `Bwd` = serveur victime ; les ports de destination sont uniques par famille (DoS 80, FTP-Patator 21, SSH-Patator 22, Heartbleed 444).
- Perturbation en espace des caractéristiques, côté Fwd seulement : remplissage `s` (longueurs Fwd × s) et délai `t` (intervalles Fwd × t), tirés dans `[1, 1+A]`, `A ∈ {0,1 ; 0,25 ; 0,5 ; 1 ; 2}`. Les dérivées sont recalculées avec des formules **mesurées** (16 de 17 du lot 1 plus la variance poolée n−1 et les moyennes IAT, toutes vérifiées à 100 % sur le train) ; les autres variables sont gelées. Candidats rejetés sans requête : hors des bornes du train, ordre vérifié violé, valeur non finie, `Fwd Packet Length Max` > 1 500 octets. Test d'identité (`s = t = 1`) : 0 écart.
- Gain en importance de XGBoost retenu : **0,1535 sur les colonnes atteignables, 0,8465 sur les colonnes gelées** (`Bwd Packet Length Std` seule : 0,5572). Les durées plafonnent à 1,2e8 µs (120 s), ce qui rejette 81 % des Slowloris et 63 % des Slowhttptest dès `t = 1,25` ; hypothèse d'un délai d'expiration, non démontrée.
- Limites : espace à deux paramètres (1 000 requêtes le couvrent presque entièrement, le budget ne contraint pas) ; pas d'ajout de paquets ; pas de variables Bwd ; attaque non reconstruite au niveau des paquets.

## 8. Résultats de l'attaque (validation, 300 flux par famille, graine 42)

- **XGBoost retenu (cible principale pré-déclarée) : 2 évasions sur 1 800** (DoS Slowhttptest à A = 1 et A = 2 ; Wilson 0,18 à 2,40 %), 0 ailleurs. La grille déterministe 31×31 sur `[1,3]²` trouve aussi 2. Un faible taux d'évasion est un résultat **conjoint** du détecteur et du modèle de menace, pas une preuve de robustesse.
- **Post hoc (décidé après avoir vu ce résultat)** : mêmes attaques contre la régression logistique et la forêt retenues. Évasion à A = 1 / A = 2 : régression logistique GoldenEye 13,7 % / 26,7 %, Hulk 5,0 % / 23,0 %, Slowhttptest 9,1 % / 24,0 %, SSH-Patator 100 % dès A = 0,5 ; forêt SSH-Patator 49,7 % / 100 %, autres ≤ 1 %. FTP-Patator jamais évadé. Hypothèse non testée : signature de taille propre à l'outil SSH-Patator (presque tous les flux ont le même `Fwd Packet Length Max`, environ 640 octets).

## 9. Durcissement (Phase 6)

Spécification `docs/hardening_specification.md` commitée avant tout code. Une copie adverse réalisable par flux d'attaque du **train** (20 tirages dans `[1,2]²`, premier candidat réalisable ; 105 045 copies, 319 flux sans candidat ; part d'attaques 15,00 % → 26,06 %), réentraînement depuis zéro. Évaluation par 4 états (original / original sous attaque / durci / durci sous attaque) avec recherche aléatoire (graine 1234) et grille jusqu'à A = 2 (A_train = 1). Rappel sur population commune (poolé), propre / aléatoire A = 2 / grille :

| Détecteur | Original | Durci |
|---|---|---|
| Régression logistique | 0,9373 / 0,6465 / 0,4911 | 0,9467 / 0,9273 / 0,9256 |
| Forêt | 0,9939 / 0,8269 / 0,8252 | 0,9950 / 0,9945 / 0,9945 |
| XGBoost | 0,9950 / 0,9945 / 0,9945 | 0,9989 / 0,9983 / 0,9983 |

Performance propre (FP/FN, original puis durci) : 509/274 puis 444/227 ; 11/40 puis 12/26 ; 7/36 puis 5/10. Sur la population d'évasion, 24 des 42 combinaisons avec évasion sont « improved » (intervalles de Wilson séparés), 18 non séparées. La régression logistique durcie garde 10,7 % d'évasion sur SSH-Patator à A = 2 (5,7 % à A = 1, dans la boîte d'entraînement).
**Contrôle post hoc (hors spécification)** : sur 20 000 flux BENIGN perturbés, la régression logistique durcie passe de 0,24 % à 2,35 % de flux signalés à A = 2 (originale : 0,21 % à 0,51 %) ; la forêt et XGBoost : 0. Changements appariés sur la validation : attaques gagnées 52 / 14 / 26 et perdues 5 / 0 / 0 (régression logistique / forêt / XGBoost).
**Limites** : évalué contre l'attaque connue (mêmes variables, même famille de perturbations), pas contre un attaquant adaptatif ; une seule graine d'entraînement ; validation déjà utilisée pour le réglage et le choix du protocole ; l'amélioration du rappel propre est inexpliquée (hypothèses : augmentation de données, rééquilibrage).

## 10. Provenance et points « post hoc » à déclarer dans le rapport

1. La **spécification d'attaque v1 n'a pas été commitée avant l'exécution** de l'attaque : elle est enregistrée rétroactivement (le dire explicitement ; l'historique Git ne prouve pas l'ordre).
2. Post hoc : choix du découpage par strate (après les résultats du jeudi) ; attaque de la régression logistique et de la forêt ; durcissement des trois détecteurs ; contrôle des flux BENIGN perturbés ; lecture secondaire « minimiser les FN ».
3. La mesure « part de flux avec au moins un candidat réalisable » est toujours 1,0 et n'est pas informative ; remplacée par la part de points réalisables de la grille.

## 11. Problèmes connus

- `src/data/audit_dataset.py` : 2 remarques ruff (I001, PYI041), à corriger **dans un commit séparé** (non lié au prétraitement).
- Avertissement de dépréciation pandas (`lsuffix`/`rsuffix`) dans `adversarial_training.py`, et RUF046 (`int(round(...))`) dans `benign_perturbation_check.py` : correctifs préparés (voir section 13), à appliquer.
- README : mis à jour jusqu'à la Phase 4.2, **périmé** depuis. Un avertissement LF/CRLF de Git sous Windows est sans danger.
- Les temps d'entraînement varient d'une exécution à l'autre (charge machine) : ne pas les comparer ni les rapporter sans mesures répétées.
- La reproductibilité de l'attaque (deux exécutions comparées par `Compare-Object`) n'a pas été vérifiée.

## 12. Ce qui reste à faire (estimations, pas des mesures : environ 18 à 26 h)

1. Vérifier l'état Git (section 3), faire les commits en attente, corriger ruff/pandas (1 h).
2. **Spécification de l'évaluation finale, commitée avant toute exécution** (0,5 h). Proposition provisoire : d'abord le segment `test` du découpage par strate, puis le vendredi à part ; chacun utilisé **une seule fois** avec les modèles et paramètres gelés. Ne rien deviner sur le contenu du vendredi.
3. Évaluation finale unique (2 à 3 h).
4. Enregistrer les agrégats dans `results/` (CSV) et produire les figures dont **la courbe de rappel selon l'amplitude avant et après durcissement** (2 à 3 h).
5. **Notebook de synthèse** (`notebooks/`), exécutable de haut en bas, avec les 12 sections du rapport (problématique, données, préparation, méthodologie, modèle de menace, modèles, attaque, défense, résultats, analyse critique, limites, conclusion) ; il lit par défaut les agrégats de `results/` et ne recalcule que sur option (6 à 8 h). Jupyter à installer après `pip install --dry-run` et approbation.
6. README complet (installation, obtention des données, reproduction) + essai de reproduction depuis un clone propre (1 à 2 h).
7. Présentation orale et questions individuelles probables (3 à 4 h).
8. Questions de compréhension (liste ci-dessous) et lignes de CV **basées uniquement sur ce qui est mesuré** (1,5 h).

Questions de compréhension à poser à la fin : (1) pourquoi `fit` sur le train et `transform` sur la validation ; (2) pourquoi exclure les ports de X ; (3) pourquoi précision 0,95 avec rappel 0,08 n'est pas un bon détecteur ; (4) pourquoi on ne peut pas dire que la stratégie de header B est meilleure que A ; (5) pourquoi le rappel plafonne entre les seuils 0,01 et 0,001 ; (6) pourquoi ne pas choisir un seuil depuis un tableau fait sur le jeudi ; (7) pourquoi la PR-AUC est le bon comparatif entre modèles ; (8) pourquoi une forêt peut rater totalement une famille jamais vue ; (9) pourquoi prévisualiser avec `--diff` avant `--fix` ; (10) pourquoi ne pas mélanger un correctif de style avec un commit de fonctionnalité ; (11) différence entre `git add` et `git commit` ; (12) pourquoi `*.csv` dans `.gitignore` ; (13) pourquoi l'attaquant ne compte que les attaques initialement détectées ; (14) pourquoi un durcissement évalué contre l'attaque connue ne prouve pas la robustesse ; (15) pourquoi une spécification commitée avant l'exécution renforce la rigueur.

## 13. Correctifs préparés mais non appliqués

- `benign_perturbation_check.py` : remplacer `PERTURB_SEED + int(round(amplitude * 100))` par `PERTURB_SEED + round(amplitude * 100)`.
- `adversarial_training.py` : remplacer `original.join(hardened, how="outer", lsuffix="_o", rsuffix="_h")` par `original.add_suffix("_o").join(hardened.add_suffix("_h"), how="outer")`.
- Ajouter à `docs/hardening_report.md` la section « Contrôle post hoc » (chiffres en section 9 de ce fichier) si elle n'y est pas.

## 14. Décisions en attente de l'étudiant

- **Date limite** du rendu (calendrier Tek-up).
- Ordre et forme de l'évaluation finale (section 12, point 2).
- Mesurer ou non le gain atteignable de la forêt (non fait, optionnel).
- Garder la règle déclarée de réglage comme résultat principal avec la lecture secondaire à côté (décision provisoire : oui).
- Hypothèse « attaquant = client initiateur » : provisoire.