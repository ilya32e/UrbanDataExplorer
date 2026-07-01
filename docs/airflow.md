# Orchestration avec Apache Airflow

Airflow industrialise le pipeline Urban Data Explorer : au lieu de lancer
manuellement `python pipeline/run_imports.py run`, le flux `download -> build ->
validate` devient un DAG planifiable, monitorable et relançable étape par étape.

## DAGs fournis

| DAG | Déclenchement | Rôle |
| --- | --- | --- |
| `urban_data_pipeline` | `@monthly` (et manuel) | Télécharge **chaque source en parallèle**, construit les zones Silver/Gold dans MySQL/MongoDB, puis valide les sorties Gold. |
| `urban_data_streaming_demo` | Manuel | Monitoring temps réel : consomme via Redis Streams les événements émis par les tâches de `urban_data_pipeline` (`pipeline:events`). |

Graphe du DAG principal :

```text
start -> [download.download_dvf_2025_paris, download.download_insee_..., ...] -> build_silver_gold -> validate_gold -> done
```

Chaque source de `config/sources.yaml` génère automatiquement sa propre tâche de
téléchargement (fan-out), ce qui rend le graphe lisible et accélère l'ingestion.

## Lancer la stack

Airflow se branche sur les services existants (MySQL, MongoDB, Redis) en
fusionnant les deux fichiers compose :

```bash
docker compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build
```

- UI Airflow : http://localhost:8080 — identifiants `airflow` / `airflow`
- API / dashboard : http://localhost:8000 (inchangé)

Sous Linux, fixez l'UID pour éviter des fichiers de logs en root :

```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
```

Sous Windows / macOS (Docker Desktop), la valeur par défaut `50000` convient.

## Utilisation

1. Ouvrir l'UI, activer le toggle du DAG `urban_data_pipeline`.
2. **Trigger DAG** pour un run immédiat, ou laisser la planification mensuelle.
3. Suivre l'avancement en vue **Graph** ; consulter les logs par tâche.

### Paramètres

Au déclenchement manuel (« Trigger DAG w/ config »), on peut passer :

```json
{ "skip_noise": true }
```

pour ignorer le calcul Bruitparif et obtenir un build plus rapide (équivalent de
`--skip-noise` du CLI). Pour le DAG streaming : `{ "count": 1000 }`.

## Comment ça marche

- L'image `airflow/Dockerfile` part de `apache/airflow:2.10.4` et ajoute les
  dépendances du pipeline (`airflow/requirements.txt`).
- Le projet est monté dans `/opt/airflow/project` et `PYTHONPATH` pointe sur
  `pipeline/src`, si bien que les DAGs importent directement les fonctions du
  CLI (`cmd_download`, `cmd_build`, `cmd_validate`) — pas de duplication de logique.
- Les connexions aux bases passent par les mêmes variables d'environnement que le
  reste du projet (`MYSQL_HOST=mysql`, `MONGO_HOST=mongo`, `REDIS_HOST=redis`…).
- Les données écrites par le build atterrissent dans `data/` du projet (volume
  monté), donc l'API les sert immédiatement.

## Architecture

- **Exécuteur** : `LocalExecutor`
- **Métadonnées Airflow** : PostgreSQL 16 dédié (`airflow-postgres`), isolé des
  bases métier MySQL/MongoDB.
- **Services** : `airflow-init` (migration + création admin), `airflow-scheduler`,
  `airflow-webserver`.
