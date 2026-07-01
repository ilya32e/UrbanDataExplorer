"""Mesure de performance de l'API Urban Data Explorer (C2.4).

Frappe les principaux endpoints en boucle, calcule des metriques de latence
(p50 / p95 / p99 / moyenne), le debit, et compare a un objectif de SLA.
Ecrit reports/benchmark.csv et affiche un tableau.

Usage :
    python scripts/benchmark.py
    python scripts/benchmark.py --base-url http://127.0.0.1:8000 --iterations 50 --sla-ms 300

Aucune dependance externe (urllib stdlib). S'authentifie en JWT si configure.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"

DEFAULT_ENDPOINTS = [
    "/health",
    "/sources",
    "/api/meta",
    "/api/overview?sales_year=2025",
    "/api/timeline?arrondissement=11",
    "/api/compare?left=11&right=18&sales_year=2025",
    "/api/map?metric=median_price_m2&level=arrondissement&year=2025",
    "/api/map?metric=median_price_m2&level=quartier&year=2025",
    "/api/map?metric=median_price_m2&level=building&year=2025",
]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, round(pct / 100.0 * (len(ordered) - 1))))
    return ordered[rank]


def measure(base_url: str, path: str, iterations: int, headers: dict[str, str]) -> dict[str, object]:
    url = base_url.rstrip("/") + path
    latencies: list[float] = []
    errors = 0
    for _ in range(iterations):
        request = urllib.request.Request(url, headers=headers)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response.read()
                if response.status >= 400:
                    errors += 1
        except (urllib.error.URLError, TimeoutError):
            errors += 1
            continue
        latencies.append((time.perf_counter() - start) * 1000.0)

    return {
        "endpoint": path,
        "samples": len(latencies),
        "errors": errors,
        "mean_ms": round(statistics.mean(latencies), 1) if latencies else float("nan"),
        "p50_ms": round(percentile(latencies, 50), 1),
        "p95_ms": round(percentile(latencies, 95), 1),
        "p99_ms": round(percentile(latencies, 99), 1),
        "max_ms": round(max(latencies), 1) if latencies else float("nan"),
        "throughput_rps": round(len(latencies) / (sum(latencies) / 1000.0), 1) if latencies else 0.0,
    }


def fetch_jwt(base_url: str) -> str | None:
    """Recupere un JWT via /auth/token (JWT = seul mecanisme d'auth).

    Renvoie None si le JWT n'est pas configure cote serveur (API ouverte) ou en cas
    d'echec. Identifiants pris dans AUTH_USERNAME / AUTH_PASSWORD (defaut urban/urban).
    """
    username = os.getenv("AUTH_USERNAME", "urban")
    password = os.getenv("AUTH_PASSWORD", "urban")
    body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/auth/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("access_token")
    except urllib.error.HTTPError as exc:
        if exc.code == 503:  # JWT non configure => API ouverte
            return None
        print(f"[benchmark] auth JWT echouee ({exc.code}), poursuite sans token.")
        return None
    except urllib.error.URLError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark de latence de l'API Urban Data Explorer.")
    parser.add_argument("--base-url", default=os.getenv("BENCH_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--warmup", type=int, default=3, help="Appels de chauffe ignores par endpoint.")
    parser.add_argument("--sla-ms", type=float, default=300.0, help="Objectif p95 (ms).")
    args = parser.parse_args()

    headers = {"Accept": "application/json"}
    token = fetch_jwt(args.base_url)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Benchmark {args.base_url}  |  {args.iterations} iterations/endpoint  |  SLA p95 < {args.sla_ms:.0f} ms\n")

    rows = []
    for path in DEFAULT_ENDPOINTS:
        measure(args.base_url, path, args.warmup, headers)  # chauffe
        result = measure(args.base_url, path, args.iterations, headers)
        verdict = "OK" if result["p95_ms"] <= args.sla_ms else "SLA KO"
        result["sla_verdict"] = verdict
        rows.append(result)
        print(
            f"  {path:<58} p50={result['p50_ms']:>6} ms  p95={result['p95_ms']:>6} ms  "
            f"p99={result['p99_ms']:>6} ms  err={result['errors']:>2}  [{verdict}]"
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORTS_DIR / "benchmark.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["endpoint", "samples", "errors", "mean_ms", "p50_ms", "p95_ms",
                        "p99_ms", "max_ms", "throughput_rps", "sla_verdict"],
        )
        writer.writeheader()
        writer.writerows(rows)

    breaches = [row for row in rows if row["sla_verdict"] != "OK"]
    print(f"\nRapport ecrit : {output}")
    print(f"SLA p95 < {args.sla_ms:.0f} ms : {len(rows) - len(breaches)}/{len(rows)} endpoints OK")
    return 1 if breaches else 0


if __name__ == "__main__":
    raise SystemExit(main())
