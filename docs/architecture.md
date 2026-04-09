# Architecture

## Objectif

Construire une plateforme data simple a faire evoluer:

- ingestion planifiee des sources ouvertes
- normalisation dans des zones Bronze, Silver puis Gold
- exposition via une API backend
- exploration cartographique dans un frontend JavaScript statique

## Organisation du depot

- `pipeline/`: scripts d'ingestion et transformations batch
- `api/`: endpoints REST pour servir les donnees nettoyees
- `frontend/`: interface HTML/CSS/JS servie directement par FastAPI
- `config/sources.toml`: catalogue minimal des sources a telecharger
- `docs/`: documentation fonctionnelle et technique

## Couches data

### Bronze

- depot des fichiers telecharges sans modification majeure
- conservation des exports d'origine pour la tracabilite
- reference geographique conservee separement

### Silver

- nettoyage des noms de colonnes
- normalisation des dates, surfaces, prix et codes geographiques
- enrichissements spatiaux par arrondissement ou IRIS

### Gold

- indicateurs agregees pour le dashboard
- tables optimisees pour les KPI, la timeline et le mode comparaison
- sorties pretes a etre servies par l'API

## Indicateurs cibles

- prix median au m2 par arrondissement
- evolution temporelle des ventes
- rapport loyer / revenu par zone
- exposition au bruit par zone

## Stack proposee

- `Python` pour le pipeline
- `FastAPI` pour le backend et le service des assets statiques
- `HTML + CSS + JavaScript + MapLibre GL` pour le frontend
