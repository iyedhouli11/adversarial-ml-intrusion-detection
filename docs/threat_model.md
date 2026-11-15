# Threat Model and Evasion Protocol — Individual Work

**Statut : modèle initial ; les variables autorisées dépendront de l'audit de contrôlabilité.**

## Objectif de l'attaquant

Faire classer comme normal un flux malveillant qui était initialement correctement classé comme attaque par le détecteur de référence. Les flux malveillants déjà mal classés ne seront pas comptés comme des évasions.

## Connaissance et accès

Le scénario initial est une attaque boîte noire à score :

- l'attaquant peut interroger le détecteur et obtenir un score ou une probabilité ;
- il ne connaît ni les paramètres, ni les variables d'entraînement, ni les données d'entraînement ;
- il travaille hors ligne sur des copies des échantillons ;
- le budget est limité à **1 000 requêtes par échantillon attaqué**.

Si une interface de score n'est pas justifiée par le déploiement simulé, un scénario à sortie de classe devra être évalué séparément plutôt que supposé équivalent.

## Capacités et restrictions

L'attaquant peut modifier uniquement les variables marquées autorisées dans `feature_controllability.md`. Chaque candidat doit respecter :

- bornes observées sur l'entraînement et contraintes de type ;
- dépendances entre durée, paquets, octets, débits et moyennes ;
- cohérence avec le protocole, l'état et le service ;
- budget de requêtes et amplitude fixée avant le test.

Les identifiants, timestamps, adresses, variables de groupe et champs dont la modification change l'identité de l'attaque sont interdits, sauf justification contraire documentée. Les exemples impossibles sont rejetés et comptés.

## Méthode prévue

La première méthode sera une recherche aléatoire de perturbations bornées. Elle sera développée et réglée sur la validation uniquement. Le modèle original, les amplitudes, le masque de variables et le budget seront gelés avant l'évaluation finale. Les échantillons originaux resteront inchangés ; les candidats modifiés seront sauvegardés séparément avec leur `sample_id`.

Cette méthode produit des attaques dans l'espace des caractéristiques. Elle ne prouve pas qu'un trafic réseau réel peut être reconstruit sans implémentation et vérification au niveau des paquets.

## Mesures

- taux d'évasion parmi les attaques initialement correctement détectées ;
- rappel avant et après attaque ;
- chute du rappel selon l'amplitude ;
- nombre médian et maximal de requêtes ;
- taux de rejet pour borne, type ou incohérence ;
- résultats par famille d'attaque lorsque les effectifs le permettent.

Les intervalles ou dénominateurs seront rapportés lorsque le nombre de cas est faible.

## Durcissement

Le premier défenseur candidat est le réentraînement avec des exemples adverses produits à partir de l'entraînement. La validation sert au choix de la configuration ; le test n'est jamais utilisé pour générer ces exemples. Le modèle durci sera évalué sur trafic normal, puis soumis à un rejeu de l'attaque sous protocole fixé.

## Limites à déclarer

Une perturbation CSV n'est pas automatiquement une modification de trafic réalisable. Les agrégats peuvent dépendre de plusieurs flux, le score peut ne pas être disponible en situation réelle et l'attaque peut être spécifique au modèle. Ces limites seront conservées dans le rapport final.

## Organisation du travail

Le modèle de menace, l'attaque, le durcissement et leur évaluation sont réalisés séquentiellement par l'auteur du projet. Les paramètres sont gelés avant le test final et les résultats sont conservés avec leur configuration exacte.


## Précisions issues de la Phase 4 (décisions provisoires, à confirmer)

- **Détecteur cible provisoire** : XGBoost, configuration retenue par la règle déclarée (profondeur 3, 100 arbres) ; forêt et régression
  logistique réservées à l'extension « transfert ».
- **Seuil de décision** : 0,5, figé. Évasion réussie = score < 0,5 pour un flux de cible 1 initialement détecté (score >= 0,5).
- **Dénominateur du taux d'évasion** : flux de cible 1 détectés à 0,5 par le modèle cible. Exclus : les flux `Attempted` (cible 0) et les
  attaques déjà non détectées (36 faux négatifs en validation pour la configuration retenue).
- **Familles attaquées** : à justifier dans le rapport (DoS volumétrique, DoS lent, force brute) ; non décidé.
- **Référence « sans effort »** : le test « une famille retirée » montre qu'un changement de famille échappe déjà au détecteur dans
  plusieurs cas (rappel 0 pour les deux Patator, partiel pour les DoS) ; point de comparaison pour l'attaque contrainte.
- **Hypothèse à valider** : attaquant = client initiateur (Fwd = attaquant, Bwd = serveur) ; les ports sont cohérents avec elle sans la prouver.
- **Dépendance du modèle** : `Bwd Packet Length Std` pèse 0,6068 du gain XGBoost (configuration profondeur 6, 200 arbres de la Phase 4.4 ;
  à recalculer pour la configuration retenue). Variable côté serveur dans l'hypothèse ci-dessus : si elle tient, la surface d'attaque est
  réduite, et un faible taux d'évasion serait un résultat du modèle de menace, pas un échec de l'attaque.