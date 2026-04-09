# API

API FastAPI qui sert a la fois les sorties Gold et le frontend statique.

## Lancement

```powershell
pip install -r api/requirements.txt
uvicorn api.app.main:app --reload
```

## Endpoints principaux

- `GET /health`
- `GET /sources`
- `GET /api/meta`
- `GET /api/overview?sales_year=2025`
- `GET /api/timeline?arrondissement=11`
- `GET /api/compare?left=11&right=18&sales_year=2025`
- `GET /api/map?metric=median_price_m2&year=2025`
- `GET /`
