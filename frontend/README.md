# Frontend

Frontend statique en JavaScript servi directement par FastAPI.

## Stack

- HTML / CSS / JavaScript natifs
- MapLibre GL via CDN
- API FastAPI pour les donnees

## Lancement

Le frontend n'est pas lance separement: il est servi par l'API FastAPI.

```powershell
uvicorn api.app.main:app --reload
```

Ou avec Docker:

```powershell
docker compose up --build -d api
```

## Acces

- page principale: `http://127.0.0.1:8000/`
- donnees: `http://127.0.0.1:8000/api/meta`

## Ce que le frontend consomme

- `GET /api/meta`
- `GET /api/overview`
- `GET /api/timeline`
- `GET /api/compare`
- `GET /api/map`
- `GET /api/reference/{level}`
