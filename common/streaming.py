"""Couche d'acces au broker de streaming (Redis Streams).

Centralise la connexion Redis et les noms de cles, sur le meme principe
12-factor que `database.py` / `document_store.py` (tout par variables d'env).

Flux `pipeline:events` : evenements *reels* emis par les taches Airflow a chaque
execution du pipeline (vrai cas d'usage streaming : la donnee nait au fil du run,
pas de replay de donnees statiques).
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import os

import redis


# Flux d'evenements du pipeline (emis par les taches Airflow).
PIPELINE_STREAM_KEY = os.getenv("PIPELINE_STREAM_KEY", "pipeline:events")
PIPELINE_GROUP = os.getenv("PIPELINE_STREAM_GROUP", "monitor")


def get_redis_url() -> str:
    explicit_url = os.getenv("REDIS_URL")
    if explicit_url:
        return explicit_url
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    return f"redis://{host}:{port}/0"


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    return redis.Redis.from_url(get_redis_url(), decode_responses=True)


def ping_redis() -> None:
    get_redis().ping()


def emit_pipeline_event(task: str, status: str, **fields: object) -> None:
    """Publie un evenement de pipeline sur le stream Redis `pipeline:events`.

    Best-effort : si Redis est indisponible, on log un avertissement sans casser la
    tache Airflow (le monitoring ne doit jamais faire echouer l'ETL). Les valeurs
    sont serialisees en chaines (contrainte des champs d'un Redis Stream).
    """
    event = {"task": str(task), "status": str(status), "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for key, value in fields.items():
        event[key] = "" if value is None else str(value)
    try:
        get_redis().xadd(PIPELINE_STREAM_KEY, event, maxlen=10_000, approximate=True)
    except redis.RedisError as exc:  # pragma: no cover - depend de l'infra
        print(f"[pipeline-event] Redis indisponible, evenement '{task}/{status}' ignore ({exc}).")


def reset_pipeline_events() -> None:
    """Vide le stream d'evenements du pipeline (demo propre)."""
    get_redis().delete(PIPELINE_STREAM_KEY)
