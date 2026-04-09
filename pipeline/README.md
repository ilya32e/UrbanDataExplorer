# Pipeline

Le pipeline gere l'ingestion des sources ouvertes et preparera les traitements Bronze/Silver/Gold.

## Commandes

```powershell
pip install -r pipeline/requirements.txt
python pipeline/run_imports.py list
python pipeline/run_imports.py download
python pipeline/run_imports.py build
```

Si aucun nom n'est passe a `download`, toutes les sources declarees dans `config/sources.yaml` sont telechargees.

Les jeux `DVF` sont filtres automatiquement sur le departement `75`.
Le build enrichit ensuite les ventes avec `adresses-ban`, un fallback `BAN PLUS`, puis les rattache aux `quartiers administratifs` et aux `IRIS` de Paris.
