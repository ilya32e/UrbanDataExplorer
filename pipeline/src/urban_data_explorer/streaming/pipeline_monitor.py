"""Consommateur de monitoring : lit en temps reel les evenements du pipeline.

Chaque tache du DAG `urban_data_pipeline` publie un evenement (`start` / `ok` /
`error`, avec la duree) sur le stream Redis `pipeline:events`. Ce module les
consomme via un **consumer group** (XREADGROUP + XACK) et fournit un resume agrege.

Contrairement au replay de donnees statiques, ces evenements sont *reellement*
generes a chaque execution du pipeline : la donnee nait au fil du run. C'est un
vrai cas d'usage streaming / traitement distribue (C2.2), applique a l'observabilite
de l'orchestration Airflow.
"""
from __future__ import annotations

import socket

import redis

from common.streaming import PIPELINE_GROUP, PIPELINE_STREAM_KEY, get_redis


def _ensure_group(client: redis.Redis) -> None:
    # id="0" : a la 1re creation, le groupe lit depuis le debut du stream (rattrape
    # les evenements deja emis par un run de pipeline anterieur au demarrage du monitor).
    try:
        client.xgroup_create(PIPELINE_STREAM_KEY, PIPELINE_GROUP, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def consume_pipeline_events(max_messages: int | None = None, block_ms: int = 2000, batch: int = 100) -> int:
    """Consomme (et affiche) les nouveaux evenements du pipeline. Renvoie le nombre traite."""
    client = get_redis()
    _ensure_group(client)
    consumer_name = f"monitor-{socket.gethostname()}"

    processed = 0
    while True:
        response = client.xreadgroup(
            PIPELINE_GROUP, consumer_name, {PIPELINE_STREAM_KEY: ">"}, count=batch, block=block_ms
        )
        if not response:
            break
        for _stream, messages in response:
            for message_id, fields in messages:
                ts = fields.get("ts", "")
                task = fields.get("task", "?")
                status = fields.get("status", "?")
                duration = fields.get("duration_ms", "")
                extra = f" ({duration} ms)" if duration else ""
                print(f"  [{ts}] {task:<28} -> {status}{extra}")
                client.xack(PIPELINE_STREAM_KEY, PIPELINE_GROUP, message_id)
                processed += 1
                if max_messages and processed >= max_messages:
                    return processed
    return processed


def pipeline_events_summary() -> dict[str, object]:
    """Agrege l'ensemble du stream (snapshot stable via XRANGE) pour un apercu global."""
    client = get_redis()
    summary: dict[str, object] = {
        "events": 0,
        "start": 0,
        "ok": 0,
        "error": 0,
        "total_duration_ms": 0,
        "tasks": [],
    }
    for _message_id, fields in client.xrange(PIPELINE_STREAM_KEY):
        summary["events"] = int(summary["events"]) + 1
        status = fields.get("status", "")
        if status in ("start", "ok", "error"):
            summary[status] = int(summary[status]) + 1
        try:
            summary["total_duration_ms"] = int(summary["total_duration_ms"]) + int(fields.get("duration_ms") or 0)
        except (TypeError, ValueError):
            pass
        if status in ("ok", "error"):
            summary["tasks"].append(  # type: ignore[union-attr]
                {"task": fields.get("task", "?"), "status": status, "duration_ms": fields.get("duration_ms", "")}
            )
    return summary
