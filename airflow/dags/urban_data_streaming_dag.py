"""DAG de monitoring streaming des evenements du pipeline (C2.2).

Declenche manuellement : consomme en temps reel, via Redis Streams, les evenements
publies par les taches du DAG `urban_data_pipeline` (start / ok / error + duree) et
affiche un resume agrege.

Cas d'usage streaming *honnete* : contrairement a un replay de donnees statiques, ces
evenements sont reellement generes a chaque execution du pipeline (la donnee nait au
fil du run). On demontre l'ingestion par messaging et le consumer group Redis, sans
broker externe expose (surface d'attaque reduite).

Demo : declencher `urban_data_pipeline`, puis ce DAG pour voir defiler ses evenements.
"""
from __future__ import annotations

from datetime import datetime
import os
import sys

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator


PROJECT_ROOT = os.getenv("UDE_PROJECT_ROOT", "/opt/airflow/project")
for path in (PROJECT_ROOT, os.path.join(PROJECT_ROOT, "pipeline", "src")):
    if path not in sys.path:
        sys.path.insert(0, path)


def monitor_pipeline_events(**context) -> None:
    from urban_data_explorer.cli import cmd_pipeline_monitor

    block_ms = int(context["params"].get("block_ms", 3000))
    code = cmd_pipeline_monitor(max_messages=None, block_ms=block_ms)
    if code:
        raise AirflowException("Echec du monitoring des evenements de pipeline")


with DAG(
    dag_id="urban_data_streaming_demo",
    description="Monitoring temps reel des evenements du pipeline (Redis Streams).",
    default_args={"owner": "urban-data-explorer"},
    start_date=datetime(2026, 1, 1),
    schedule=None,  # declenchement manuel
    catchup=False,
    tags=["urban-data-explorer", "streaming", "redis", "monitoring"],
    params={"block_ms": 3000},
) as dag:

    monitor = PythonOperator(task_id="monitor_pipeline_events", python_callable=monitor_pipeline_events)
