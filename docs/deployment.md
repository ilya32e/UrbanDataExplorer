# Deployment

## Etat actuel

Le projet est pleinement executable en local:

```powershell
python pipeline/run_imports.py download
python pipeline/run_imports.py build
python -m uvicorn api.app.main:app --reload
```

Le dashboard web est donc operationnel avec des jeux de donnees realistes, mais le repo ne contient pas encore de deploiement public automatise.

## Pourquoi le deploiement public demande une etape supplementaire

Le repo ne versionne pas les artefacts `Bronze`, `Silver` et `Gold`. Ce choix est volontaire:

- ne pas alourdir le depot Git
- rester conforme a une logique de regeneration locale
- eviter de pousser de gros fichiers techniques dans le repo

Consequence:

- un hebergeur public doit soit reconstruire les donnees au build
- soit recevoir des artefacts `Gold` preconstruits

## Deux strategies possibles

### Strategie A: build de donnees pendant le deploiement

Principe:

- le service recupere les sources ouvertes
- lance le pipeline
- demarre ensuite FastAPI

Avantages:

- reproductibilite forte
- pas besoin de stocker les sorties `Gold` ailleurs

Limites:

- temps de build plus long
- dependance a la disponibilite des sources ouvertes
- cout potentiellement plus eleve sur plateforme cloud

### Strategie B: publier des artefacts Gold de test

Principe:

- construire localement un jeu `Gold` de test
- le stocker dans un bucket, un stockage objet ou un package de release
- faire lire ces artefacts par l'API de production

Avantages:

- deploiement plus rapide
- demo plus stable
- moins de dependances runtime

Limites:

- il faut definir un cycle de mise a jour
- la gouvernance des artefacts doit etre explicite

## Recommandation pour une presentation

Pour un rendu de type cours / jury, la meilleure strategie est souvent:

1. garder une version locale parfaitement fonctionnelle pour la demo live
2. publier une version web appuyee sur des artefacts `Gold` de test preconstruits
3. expliquer clairement que les donnees peuvent etre regenerees via le pipeline

## Ce qu'il reste a choisir

- plateforme de deploiement: Render, Railway, Fly.io, VM perso, autre
- strategie de disponibilite des artefacts `Gold`
- eventuel niveau de refresh des donnees

## Message a utiliser pendant la presentation

`Le projet est deployable, mais nous avons volontairement separe le code source du stockage des donnees generees. Cela garde le repo propre et reproductible, tout en laissant ouverte la strategie de publication des artefacts de test.`
