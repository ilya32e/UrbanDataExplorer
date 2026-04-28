# Pipeline

Le pipeline gere l'ingestion des sources ouvertes et prepare les traitements Bronze/Silver/Gold, avec ecriture des tables analytiques dans `MySQL` et des documents `GeoJSON/JSON` dans `MongoDB`.

## Commandes

### En local

```powershell
pip install -r pipeline/requirements.txt
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_DATABASE="urban_data_explorer"
$env:MYSQL_USER="urban"
$env:MYSQL_PASSWORD="urban"
$env:MONGO_HOST="127.0.0.1"
$env:MONGO_PORT="27017"
$env:MONGO_DATABASE="urban_data_explorer"
python pipeline/run_imports.py list
python pipeline/run_imports.py download
python pipeline/run_imports.py build
```

### Avec Docker

```powershell
docker compose run --rm pipeline python pipeline/run_imports.py list
docker compose run --rm pipeline python pipeline/run_imports.py download
docker compose run --rm pipeline python pipeline/run_imports.py build
```

Si aucun nom n'est passe a `download`, toutes les sources declarees dans `config/sources.yaml` sont telechargees.

Les jeux `DVF` sont filtres automatiquement sur le departement `75`.
Le build enrichit ensuite les ventes avec `adresses-ban`, un fallback `BAN PLUS`, puis les rattache aux `quartiers administratifs` et aux `IRIS` de Paris.

## Sorties produites

- `MySQL` pour les tables `Silver` et `Gold`
- `MongoDB` pour les couches `GeoJSON` et les metadonnees `JSON`
- `Bronze` conserve les fichiers bruts telecharges localement
