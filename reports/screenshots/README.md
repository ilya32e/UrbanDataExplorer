# Preuves techniques — Urban Data Explorer

Captures d'écran générées à partir des **conteneurs réellement en cours d'exécution**
(stack `docker compose`), pour servir de preuve des compétences techniques du projet.
Toutes les données proviennent de commandes live (`docker exec`, `curl`, Swagger), aucune n'est fabriquée.

| # | Preuve | Fichier | Source de la capture |
|---|--------|---------|----------------------|
| 1 | **Base relationnelle** (MySQL 8.0) | [`01_mysql_relational.png`](01_mysql_relational.png) | `SHOW TABLES` / `SHOW KEYS` / `COUNT(*)` — 21 tables Silver+Gold, PK composite `(arrondissement, year)`, index BTREE |
| 2 | **Base NoSQL** (MongoDB 7) | [`02_mongodb_nosql.png`](02_mongodb_nosql.png) | `getCollectionNames` / `countDocuments` / `getIndexes` — 6 collections GeoJSON (8 325 docs), index secondaires |
| 3 | **API REST** (FastAPI) | [`03_api_swagger.png`](03_api_swagger.png) | Swagger UI live `http://localhost:8000/docs` — OAS 3.1, endpoints health/auth/sources/dashboard |
| 4 | **Pipelines / Orchestration** (Apache Airflow) | [`04_pipelines_airflow.png`](04_pipelines_airflow.png) | `airflow dags list` / `list-runs` — 2 DAGs, run `success`, métriques ETL |
| 5 | **Monitoring & performance** | [`05_monitoring_metrics.png`](05_monitoring_metrics.png) | `GET /metrics` (live) + `benchmark.csv` (p50/p95/p99 + SLA) + `pipeline_metrics.csv` |

## Reproduire les preuves

```powershell
# Démarrer la stack
docker compose up -d

# 1. Relationnel (MySQL)
docker exec urbandataexplorer-mysql-1 mysql -uurban -purban urban_data_explorer -e "SHOW TABLES; SHOW KEYS FROM gold_sales_yearly;"

# 2. NoSQL (MongoDB)
docker exec urbandataexplorer-mongo-1 mongosh urban_data_explorer --eval "db.getCollectionNames()"

# 3. API (Swagger) -> http://localhost:8000/docs

# 4. Pipelines (Airflow)
docker exec urbandataexplorer-airflow-scheduler-1 airflow dags list

# 5. Monitoring & perf
curl http://localhost:8000/metrics
python scripts/benchmark.py --iterations 40 --sla-ms 300   # -> reports/benchmark.csv
python pipeline/run_imports.py build                        # -> reports/pipeline_metrics.csv
```

> Captures générées le 2026-06-29.
