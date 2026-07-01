"""Watcher temps reel des evenements du pipeline (demo streaming Redis, C2.2).

A lancer AVANT de declencher le DAG `urban_data_pipeline` : le watcher se met en
attente bloquante (`XREADGROUP ... BLOCK`) et affiche chaque evenement **a l'instant
ou la tache correspondante se termine** — pas a la fin. C'est ce qui demontre le
caractere temps reel (par opposition a une lecture batch de tout le backlog).

Usage (dans un terminal, cote hote) :

    docker compose -f docker-compose.yml -f docker-compose.airflow.yml \
        exec -w /opt/airflow/project airflow-scheduler \
        python scripts/stream_watch.py --timeout 300

Puis, dans un 2e terminal (ou via l'UI Airflow), declenche le pipeline :

    docker compose -f docker-compose.yml -f docker-compose.airflow.yml \
        exec airflow-scheduler airflow dags trigger urban_data_pipeline

Options :
    --timeout N     duree totale d'ecoute en secondes (defaut 300, Ctrl+C pour stopper).
    --group NOM     nom du consumer group (defaut "watch", independant du DAG).
    --from-start    lit aussi les evenements deja presents (backlog) avant l'ecoute.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

sys.path.insert(0, "/opt/airflow/project")
sys.path.insert(0, "/opt/airflow/project/pipeline/src")

import redis  # noqa: E402

from common.streaming import PIPELINE_STREAM_KEY, get_redis  # noqa: E402


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Watcher temps reel des evenements du pipeline.")
    parser.add_argument("--timeout", type=int, default=300, help="Duree totale d'ecoute (s).")
    parser.add_argument("--group", default="watch", help="Nom du consumer group.")
    parser.add_argument("--from-start", action="store_true", help="Inclure le backlog deja present.")
    args = parser.parse_args()

    client = get_redis()
    start_id = "0" if args.from_start else "$"  # "$" = uniquement les nouveaux evenements
    try:
        client.xgroup_create(PIPELINE_STREAM_KEY, args.group, id=start_id, mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise  # le groupe existe deja : on reprend la ou il en etait

    print(f">>> Watcher en ecoute (group='{args.group}') — declenche maintenant 'urban_data_pipeline'.")
    print(f">>> Attente bloquante XREADGROUP BLOCK, pendant {args.timeout}s (Ctrl+C pour arreter).\n", flush=True)

    deadline = time.monotonic() + args.timeout
    received = {"events": 0, "ok": 0, "error": 0}
    try:
        while time.monotonic() < deadline:
            response = client.xreadgroup(
                args.group, "watcher", {PIPELINE_STREAM_KEY: ">"}, count=10, block=2000
            )
            if not response:
                continue  # rien de neuf : on reste en attente jusqu'au timeout
            for _stream, messages in response:
                for message_id, fields in messages:
                    task = fields.get("task", "?")
                    status = fields.get("status", "?")
                    duration = fields.get("duration_ms", "")
                    extra = f" ({duration} ms)" if duration else ""
                    marker = "OK " if status == "ok" else ("ERR" if status == "error" else "...")
                    print(f"  [{_now()}]  {marker}  {task:<28} -> {status}{extra}", flush=True)
                    client.xack(PIPELINE_STREAM_KEY, args.group, message_id)
                    received["events"] += 1
                    if status in received:
                        received[status] += 1
    except KeyboardInterrupt:
        print("\n>>> Interrompu.")

    print(
        f"\n--- Fin de l'ecoute --- {received['events']} evenement(s) recu(s) en direct "
        f"({received['ok']} ok, {received['error']} erreur(s))."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
