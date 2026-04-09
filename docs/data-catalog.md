# Mini Data Catalog

## Objectif

Ce document explique:

- quelles sources ouvertes sont mobilisees
- pourquoi elles ont ete retenues
- a quelle maille elles sont exploitees
- quelles limites ou biais elles introduisent

L'idee n'est pas seulement de lister des datasets, mais de justifier leur usage analytique dans le projet.

## Criteres de selection des sources

Les sources ont ete choisies selon quatre criteres:

- pertinence metier pour expliquer le logement parisien
- granularite suffisante pour produire une demo convaincante
- accessibilite en open data et reproductibilite du telechargement
- compatibilite geographique avec des jointures a Paris

## Sources principales

| Source | Usage | Niveau geographique | Format | Pourquoi ce choix |
| --- | --- | --- | --- | --- |
| DVF 2023-2025 | Transactions immobilieres, prix au m2, volumes, surfaces | adresse / mutation | TXT ZIP | reference publique la plus naturelle pour observer les ventes reelles |
| INSEE Filosofi 2021 | Revenus, niveau de vie, part imposable, pauvrete | IRIS | CSV ZIP | apporte le contexte socio-economique necessaire pour relier prix et pouvoir d'achat |
| Paris Data - Encadrement des loyers | Loyers de reference et effort locatif | quartier | CSV | permet de comparer achat et location avec une source officielle parisienne |
| Paris Data - Logements sociaux finances | Effort annuel de production sociale | arrondissement / programme | CSV | ajoute une lecture d'offre publique et de politique du logement |
| Bruitparif 2024 | Composantes du score de qualite de vie | couche SIG / zone | XLSX + ZIP | apporte la dimension environnementale que n'offrent pas les sources immobilieres classiques |
| Adresses BAN Paris | Geolocalisation des ventes DVF | adresse | CSV | necessaire pour passer d'une lecture par arrondissement a des mailles plus fines |

## Sources de reference geographique

| Source | Usage | Niveau geographique | Format | Pourquoi ce choix |
| --- | --- | --- | --- | --- |
| Arrondissements de Paris | Fond cartographique principal | arrondissement | GeoJSON | unite administrative la plus lisible pour le dashboard principal |
| Quartiers administratifs de Paris | Aggregation fine des prix | quartier | GeoJSON | niveau plus fin que l'arrondissement, encore comprehensible en soutenance |
| Voies de Paris | Representation lineaire des rues | rue | GeoJSON | evite de reduire la rue a un point et renforce la qualite visuelle de la carte |
| IRIS Paris | Enrichissements statistiques fins | IRIS | CSV avec geometries | indispensable pour relier Filosofi a des zones coherentes |

## Service complementaire

| Source | Usage | Pourquoi ce choix |
| --- | --- | --- |
| BAN Plus - lien adresse parcelle | fallback de geocodage | permet de rattraper une partie des ventes DVF non matchees directement avec `adresses-ban` |

## Justification par besoin analytique

### 1. Mesurer les prix et les dynamiques du marche

Source cle:

- `DVF`

Pourquoi:

- donne des ventes observees et non des annonces
- permet de calculer `median_price_m2`, `transactions`, `median_surface_m2`
- fournit une vraie serie temporelle 2023-2025

Limites:

- bruit sur certaines mutations atypiques
- necessite un filtrage fort
- couverture limitee au marche de vente

### 2. Relier le logement au niveau de vie

Source cle:

- `INSEE Filosofi`

Pourquoi:

- fournit un contexte socio-economique robuste
- permet des indicateurs lisibles pour la narration: revenu median, pauvrete, part imposable
- fait le lien entre accessibilite du logement et structure sociale des quartiers

Limites:

- millesime non synchrone avec toutes les autres sources
- lecture statique plutot que pleinement temporelle

### 3. Comparer achat et location

Source cle:

- `Paris Data - Encadrement des loyers`

Pourquoi:

- source officielle adaptee au contexte parisien
- utile pour construire un indicateur d'effort locatif simple a expliquer

Limites:

- loyers de reference administratifs, pas loyers de marche observes
- maille quartier, donc moins fine que certaines sorties DVF

### 4. Ajouter la dimension d'action publique

Source cle:

- `Paris Data - Logements sociaux finances`

Pourquoi:

- apporte une lecture de production sociale, absente des datasets prix / loyers
- utile pour comparer dynamiques de marche et effort d'investissement public

Limites:

- mesure des logements finances, pas du stock total de parc social
- interpretation necessite prudence d'une annee a l'autre

### 5. Ajouter la qualite de vie environnementale

Source cle:

- `Bruitparif`

Pourquoi:

- apporte des signaux differenciants pour la demo
- permet de sortir d'un dashboard purement prix / revenu
- justifie un indicateur composite `quality_of_life_score`

Limites:

- indicateur derive, avec ponderations assumees
- forte dimension methodologique a expliciter pendant la soutenance

### 6. Descendre a des mailles fines

Sources cles:

- `adresses-ban`
- `BAN Plus`
- `quartier_paris`
- `voie_paris`
- `iris_paris`

Pourquoi:

- rendent possible une carte plus ambitieuse qu'un simple choropleth par arrondissement
- permettent de produire des vues `quartier`, `street`, `building`
- renforcent l'effet de demo live

Limites:

- geocodage imparfait par nature
- le niveau `building` reste un proxy d'adresse / batiment, pas une reference fonciere parfaite

## Qualite de vie

Le dashboard n'expose plus separement `noise_score`, `air_score`, `high_noise_share_pct` et `environmental_pressure_index`. Ces composantes sont consolidees dans un seul indicateur:

```text
quality_of_life_score = 10 * (
  0.30 * noise_norm +
  0.30 * air_norm +
  0.25 * high_noise_norm +
  0.15 * env_norm
)
```

Lecture du score:

- `0` proche d'une situation environnementale tres defavorable
- `10` proche d'une situation environnementale tres favorable

Pourquoi ce choix:

- simplifier la lecture pour l'utilisateur final
- garder une methode explicable pendant la soutenance
- eviter un dashboard surcharge par plusieurs metriques tres techniques

## Remarques finales

- `DVF` reste la source la plus structurante du projet
- `Filosofi` donne la profondeur socio-economique necessaire au storytelling
- `Bruitparif` rend la demo plus originale et plus complete
- `BAN` et les referentiels geographiques donnent au projet sa finesse spatiale

L'ensemble forme un compromis realiste entre robustesse analytique, disponibilite open data et qualite de demonstration.
