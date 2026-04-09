# Mini Data Catalog

## Sources principales

| Source | Usage | Niveau geographique | Format |
| --- | --- | --- | --- |
| DVF 2023-2025 | Transactions immobilieres, prix au m2, timeline | adresse / mutation | TXT ZIP |
| INSEE Filosofi 2021 | Revenus et accessibilite du logement | IRIS | CSV ZIP |
| Paris Data - Encadrement des loyers | Loyers de reference et comparaison achat/location | quartier | CSV |
| Paris Data - Logements sociaux finances | Production de logements sociaux par arrondissement et par annee | arrondissement / programme | CSV |
| Bruitparif 2024 | Composantes du score de qualite de vie | couche SIG / zone | XLSX + ZIP |
| Adresses BAN Paris | Geolocalisation fine des ventes DVF | adresse | CSV |

## Source de reference

| Source | Usage | Niveau geographique | Format |
| --- | --- | --- | --- |
| Arrondissements de Paris | Choroplethes et jointures spatiales | arrondissement | GeoJSON |
| Quartiers administratifs de Paris | Agragation des prix par quartier | quartier | GeoJSON |
| IRIS Paris | Enrichissements spatiaux fins et croisement avec Filosofi | IRIS | CSV avec geometries |

## Remarques

- `DVF` est volumineux: le script filtre ensuite le departement `75` et construit une serie 2023-2025.
- `Filosofi` sert a relier les prix du logement au niveau de vie local.
- `Paris Data - Logements sociaux finances` mesure l'effort annuel de production sociale, pas le stock total de parc social.
- `Bruitparif` fournit les composantes air / bruit qui alimentent un indicateur composite `quality_of_life_score`.
- `Adresses BAN Paris` sert au rattachement d'une vente DVF a un point, avec un fallback `BAN PLUS` par parcelle quand l'adresse ne matche pas directement.
- Les arrondissements restent utiles pour le dashboard principal, mais les sorties `quartier` et `IRIS` sont maintenant produites pour une lecture plus fine du marche.

## Qualite de vie

Le dashboard n'expose plus separement les metriques `noise_score`, `air_score`, `high_noise_share_pct` et `environmental_pressure_index`. Elles sont consolidees dans un score unique:

```text
quality_of_life_score = 10 * (
  0.30 * noise_norm +
  0.30 * air_norm +
  0.25 * high_noise_norm +
  0.15 * env_norm
)
```

Les coefficients privilegient les signaux les plus directement percus au quotidien, tout en conservant un poids plus faible pour l'indice de synthese afin d'eviter un double comptage des effets air / bruit.
