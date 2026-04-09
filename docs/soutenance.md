# Soutenance

## Angle narratif

Le fil rouge recommande:

`Paris est un marche du logement tres visible, mais difficile a lire proprement sans croiser plusieurs sources. Notre projet transforme cette complexite en un dashboard unique, lisible et demonstrable.`

## Structure de presentation

### 1. Le probleme

Message:

- les donnees existent, mais elles sont dispersees
- prix seuls = vision incomplete
- il faut relier ventes, revenus, loyers, logement social et qualite de vie

Phrase utile:

`Notre objectif n'etait pas juste de faire une carte, mais de construire une lecture data coherente du logement parisien.`

### 2. La promesse du projet

Message:

- une seule application
- plusieurs sources ouvertes
- plusieurs mailles geographiques
- une interface qui sert autant l'analyse que la demo

### 3. La logique data

Message:

- `Bronze`: on conserve les sources
- `Silver`: on nettoie et on enrichit
- `Gold`: on produit les artefacts prets pour le dashboard

Transition:

`On a choisi une architecture simple a expliquer, mais suffisamment solide pour produire des sorties reutilisables.`

### 4. La valeur analytique

Message:

- `DVF` pour les ventes reelles
- `Filosofi` pour le niveau de vie
- `Loyers` pour l'effort locatif
- `Logement social` pour l'action publique
- `Bruitparif` pour la qualite de vie

### 5. La demo produit

Ordre recommande:

1. ouvrir la home et montrer la carte principale
2. changer la metrique cartographique
3. comparer deux arrondissements
4. ouvrir la timeline
5. passer sur un niveau plus fin: `quartier`, puis `street`, puis `building`
6. finir sur les sources et la tracabilite

## Script de demo live

### Intro de demo

`On va maintenant passer d'une logique de sources brutes a une logique d'usage concret.`

### Sequence 1: vue globale

A montrer:

- carte par arrondissement
- KPIs de synthese
- choix d'une metrique lisible, par exemple `median_price_m2`

Ce qu'il faut dire:

- la ville est visible en un coup d'oeil
- on obtient une premiere hierarchie des arrondissements

### Sequence 2: comparaison

A montrer:

- `Arrondissement A` vs `Arrondissement B`

Ce qu'il faut dire:

- on ne regarde pas seulement les prix
- on relie prix, revenu, logement social et qualite de vie

### Sequence 3: temporalite

A montrer:

- timeline des ventes
- timeline du logement social
- timeline des loyers

Ce qu'il faut dire:

- on passe d'une photo statique a une lecture dynamique

### Sequence 4: finesse spatiale

A montrer:

- `quartier`
- `street`
- `building`

Ce qu'il faut dire:

- l'arrondissement est utile pour lire vite
- les niveaux fins rendent la plateforme plus analytique et plus demonstrative

### Sequence 5: transparence

A montrer:

- section des sources
- docs du repo

Ce qu'il faut dire:

- chaque indicateur est relie a des sources ouvertes identifiees
- les choix de ponderation et de transformation sont documentes

## Messages cle a marteler

- le projet n'empile pas des datasets, il les relie
- l'architecture est simple mais volontaire
- la qualite de vie enrichit la lecture purement immobiliere
- les mailles fines donnent une vraie valeur de demo
- le repo reste reproductible: on peut retelecharger et reconstruire les donnees

## Questions probables du jury

### Pourquoi ces sources

Reponse courte:

`Parce qu'elles couvrent les dimensions essentielles du sujet: marche, revenus, loyers, action publique et environnement.`

### Pourquoi pas une base de donnees

Reponse courte:

`Pour ce niveau de volumetrie et pour une soutenance, les artefacts Gold suffisent et rendent la chaine plus simple a expliquer et a maintenir.`

### Pourquoi un score composite de qualite de vie

Reponse courte:

`Pour simplifier la lecture utilisateur tout en gardant une formule transparente et documentee.`

### Quelles limites

Reponse courte:

`Le deploiement public reste a finaliser et certains indicateurs, notamment environnementaux, reposent sur des choix methodologiques assumes.`

## Cloture recommandee

`Urban Data Explorer montre qu'on peut transformer un ensemble de sources ouvertes heterogenes en un produit data lisible, reproductible et demonstrable, avec une architecture simple mais credible.`
