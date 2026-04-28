# API

API FastAPI qui sert a la fois les tables `Gold` stockees dans `MySQL`, les documents cartographiques stockes dans `MongoDB`, et le frontend statique.

## Lancement

### En local

```powershell
pip install -r api/requirements.txt
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_DATABASE="urban_data_explorer"
$env:MYSQL_USER="urban"
$env:MYSQL_PASSWORD="urban"
$env:MONGO_HOST="127.0.0.1"
$env:MONGO_PORT="27017"
$env:MONGO_DATABASE="urban_data_explorer"
uvicorn api.app.main:app --reload
```

### Avec Docker

```powershell
docker compose up --build -d api
docker compose ps
```

## Verification

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/meta
```

## Endpoints principaux

- `GET /health`
- `GET /sources`
- `GET /api/meta`
- `GET /api/overview?sales_year=2025`
- `GET /api/timeline?arrondissement=11`
- `GET /api/compare?left=11&right=18&sales_year=2025`
- `GET /api/map?metric=median_price_m2&level=arrondissement&year=2025`
- `GET /api/reference/quartier`
- `GET /`
