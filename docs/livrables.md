# Livrables

## Vue rapide

| Livrable | Statut | Preuve / emplacement |
| --- | --- | --- |
| 1. Code source complet (pipeline + API + front) | Pret | `pipeline/`, `api/`, `frontend/`, repo GitHub |
| 2. Documentation d'architecture & schemas data | Pret | `docs/architecture.md` |
| 3. Mini data catalog + justification des sources / choix | Pret | `docs/data-catalog.md` |
| 4. Dashboard web deploye avec jeux de test realistes | Partiellement pret | application locale fonctionnelle, repo GitHub pret; deploiement public a finaliser selon plateforme choisie |

## Detail par livrable

### 1. Code source complet

Le code est structure par couches:

- `pipeline/`: ingestion, build Bronze / Silver / Gold
- `api/`: endpoints FastAPI
- `frontend/`: dashboard web statique

Le depot distant:

- `https://github.com/ilya32e/UrbanDataExplorer.git`

### 2. Documentation d'architecture & schemas data

Document principal:

- `docs/architecture.md`

Contenu:

- vue systeme
- architecture des composants
- cycle de vie des donnees
- schema de donnees simplifie
- choix d'architecture et limites

### 3. Mini data catalog + justification

Document principal:

- `docs/data-catalog.md`

Contenu:

- liste des sources
- usage analytique
- maille geographique
- justification de selection
- limites et biais

### 4. Dashboard web deploye

Etat actuel:

- dashboard local fonctionnel via FastAPI
- jeux de test realistes regenerables avec:
  - `python pipeline/run_imports.py download`
  - `python pipeline/run_imports.py build`
- repo public pret pour servir de base de deploiement

Point restant:

- choisir une plateforme de deploiement public compatible avec un build de donnees ou avec des artefacts `Gold` preconstruits

## Recommandation

Pour une remise propre, les livrables `1`, `2` et `3` sont deja presentables dans le repo.

Le livrable `4` est techniquement pret localement, mais la publication web depend encore d'une decision de plateforme et d'une strategie de mise a disposition des donnees de test.
