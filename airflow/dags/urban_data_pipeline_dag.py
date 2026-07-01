"""DAG principal Urban Data Explorer : download -> build -> validate.

Ce DAG orchestre le meme flux que `python pipeline/run_imports.py run`, mais en
exposant chaque etape comme une tache Airflow. Les telechargements de sources
sont parallelises (un task par source) pour montrer un vrai graphe d'ingestion,
puis le build Silver/Gold attend que toutes les sources soient disponibles, et la
validation cloture le run.

Le package metier `urban_data_explorer` est importe directement : le projet est
monte dans le conteneur Airflow et `PYTHONPATH` pointe sur `pipeline/src`.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import time
import os
import sys

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup


# --- Acces au package metier monte dans le conteneur ---------------------------
PROJECT_ROOT = os.getenv("UDE_PROJECT_ROOT", "/opt/airflow/project")
for path in (PROJECT_ROOT, os.path.join(PROJECT_ROOT, "pipeline", "src")):
    if path not in sys.path:
        sys.path.insert(0, path)


# --- Emission d'evenements temps reel sur Redis Streams (C2.2) ------------------
def _tracked(task_name: str, action, context: dict) -> None:
    """Execute `action` en publiant des evenements start/ok/error sur `pipeline:events`.

    Ces evenements sont *reellement* generes au fil du run (vrai streaming, pas un
    replay). Le monitoring est best-effort : il n'empeche jamais la tache d'aboutir.
    """
    from common.streaming import emit_pipeline_event

    run_id = context.get("run_id") or ""
    emit_pipeline_event(task=task_name, status="start", run_id=run_id)
    started = time.perf_counter()
    try:
        action()
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        emit_pipeline_event(task=task_name, status="error", run_id=run_id, duration_ms=duration_ms, detail=str(exc)[:200])
        raise
    duration_ms = int((time.perf_counter() - started) * 1000)
    emit_pipeline_event(task=task_name, status="ok", run_id=run_id, duration_ms=duration_ms)


def _list_source_names() -> list[str]:
    """Lit les sources configurees pour generer une tache de download par source.

    Lue au parse du DAG : si la config n'est pas encore montee, on retombe sur un
    unique download global plutot que de casser l'affichage du DAG.
    """
    try:
        from urban_data_explorer.config import load_sources

        return list(load_sources().keys())
    except Exception:  # parse-time safe : la config peut manquer hors conteneur
        return []


# --- Callables des taches (executes par le worker, pas au parse) ---------------
def download_one(source_name: str, **context) -> None:
    from urban_data_explorer.cli import cmd_download

    def action() -> None:
        if cmd_download([source_name], force=False):
            raise AirflowException(f"Echec du telechargement de la source {source_name!r}")

    _tracked(f"download_{source_name}", action, context)


def download_all(**context) -> None:
    from urban_data_explorer.cli import cmd_download

    def action() -> None:
        if cmd_download([], force=False):
            raise AirflowException("Echec du telechargement des sources")

    _tracked("download_all", action, context)


def build_gold_zone(**context) -> None:
    from urban_data_explorer.cli import cmd_build

    skip_noise = bool(context["params"].get("skip_noise", False))

    def action() -> None:
        if cmd_build(skip_noise=skip_noise):
            raise AirflowException("Echec du build Silver/Gold")

    _tracked("build_silver_gold", action, context)


def validate_outputs(**context) -> None:
    from urban_data_explorer.cli import cmd_validate

    def action() -> None:
        if cmd_validate(quiet=False):
            raise AirflowException("Validation des sorties Gold echouee")

    _tracked("validate_gold", action, context)


default_args = {
    "owner": "urban-data-explorer",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="urban_data_pipeline",
    description="Ingestion open data Paris puis build Silver/Gold et validation.",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@monthly",
    catchup=False,
    max_active_runs=1,
    tags=["urban-data-explorer", "etl", "medallion"],
    params={"skip_noise": False},
) as dag:

    start = EmptyOperator(task_id="start")

    with TaskGroup(group_id="download", tooltip="Telechargement des sources open data") as download_group:
        source_names = _list_source_names()
        if source_names:
            for name in source_names:
                PythonOperator(
                    task_id=f"download_{name}",
                    python_callable=download_one,
                    op_kwargs={"source_name": name},
                )
        else:
            PythonOperator(task_id="download_all", python_callable=download_all)

    build = PythonOperator(task_id="build_silver_gold", python_callable=build_gold_zone)
    validate = PythonOperator(task_id="validate_gold", python_callable=validate_outputs)
    done = EmptyOperator(task_id="done")

    start >> download_group >> build >> validate >> done
