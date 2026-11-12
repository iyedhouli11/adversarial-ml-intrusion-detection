# Adversarial Machine Learning for Network Intrusion Detection

**Protocole initial proposé — validation du 13 novembre 2026**
**Statut : méthode planifiée ; aucune expérience ni métrique n'a encore été exécutée.**

## Problématique

Un système de détection d'intrusion doit distinguer les flux normaux des flux malveillants. Nous étudions une attaque d'évasion : un attaquant modifie certaines caractéristiques d'un trafic malveillant, dans des limites réalistes, afin qu'il soit classé comme normal. L'expérience est réalisée hors ligne, sur des données publiques, sans attaquer un système réel.

## Données et formulation

Le candidat provisoire est CIC-IDS2017, publié par le Canadian Institute for Cybersecurity. Il contient des flux normaux et plusieurs familles d'attaques, décrits par plus de 80 variables de flux. Les captures couvrent cinq jours ; le lundi est annoncé comme normal et les attaques sont réparties du mardi au vendredi. Cette structure permet d'étudier un découpage par jour.

Le problème principal sera binaire : **Normal = 0** et **Attack = 1**. Les familles seront regroupées pour l'apprentissage principal puis analysées séparément. Le choix définitif dépendra d'un audit des doublons, valeurs manquantes ou infinies, étiquettes, variables identifiantes et relations entre variables dérivées. Une analyse publiée signale des problèmes de capture, de duplication de paquets et d'étiquetage dans CIC-IDS2017 ; ces limites seront vérifiées et documentées.

## Préparation et découpage

Les variables utilisées par le détecteur et les variables modifiables par l'attaquant sont deux décisions distinctes. Une variable non modifiable peut rester une entrée du détecteur si elle est observable en fonctionnement et ne constitue pas une fuite ou un artefact ; elle sera simplement interdite dans l'attaque. Les transformations seront intégrées dans une pipeline et ajustées sur l'entraînement uniquement.

Le découpage **proposé mais non finalisé** est : entraînement lundi-mardi-mercredi, validation jeudi, test final vendredi. Les jours et familles présents seront confirmés après inspection des métadonnées. Une faisabilité spécifique sera exigée avant l'attaque : nombre de flux malveillants par jour et par famille, nombre de ces flux correctement détectés initialement, et incertitude de l'estimation. Si jeudi contient trop peu de cas correctement détectés, un sous-ensemble d'attaque séparé par session ou période sera défini sans utiliser vendredi.

## Modèles et métriques

La baseline sera une régression logistique, comparée à une forêt aléatoire et à XGBoost. Le réglage utilisera uniquement l'entraînement et la validation ; le test final ne servira qu'à l'évaluation finale. Nous présenterons la matrice de confusion, précision, rappel, F1-score, PR-AUC, temps d'entraînement et temps d'inférence, ainsi qu'une discussion du coût des faux positifs et faux négatifs. Aucun résultat ne sera écrit avant exécution réelle.

## Menace, évasion et durcissement

L'attaquant connaît les scores renvoyés par le détecteur, mais pas ses paramètres ni ses données d'entraînement. Il dispose d'au plus **1 000 requêtes par échantillon**. La première méthode prévue est une recherche aléatoire de perturbations bornées, appliquée uniquement aux variables autorisées par l'audit de contrôlabilité. Une évasion compte seulement pour un flux malveillant initialement correctement détecté qui devient normal. Nous mesurerons le taux d'évasion, la chute du rappel selon l'amplitude, le nombre de requêtes et les rejets pour incohérence.

Ces expériences sont des **attaques dans l'espace des caractéristiques** : elles modifient des lignes de variables de flux. Elles ne seront pas présentées comme une modification de paquets ou une reconstruction de trafic réel tant qu'une telle reconstruction n'aura pas été implémentée et vérifiée. Le durcissement initial prévu est un réentraînement avec des exemples adverses produits à partir de l'entraînement uniquement, suivi d'un rejeu de l'attaque et d'une comparaison des performances normales.

## Reproductibilité

Les graines, versions, configurations et procédures d'acquisition seront enregistrées. Les données brutes et traitées resteront hors du dépôt Git. Le dépôt et les notebooks seront complétés après validation du schéma des données. À ce stade, le dépôt contient uniquement la documentation préparatoire.

**Références :** [CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) ; Lanvin et al., *Errors in the CICIDS2017 dataset and the significant differences in detection performances it makes*, DOI `10.1007/978-3-031-31108-6_2`.
