"""Securite et observabilite de l'API.

Deux mecanismes d'observabilite/protection, activables par variables d'environnement :

1. Rate-limiting par IP (fenetre glissante en memoire) -> couvre C2.1 / C2.4.
2. Mesure du temps de traitement + log des requetes lentes -> couvre C2.4 / monitoring C1.4.

L'authentification est geree uniquement par JWT / OAuth2 (voir `auth.py`).
"""
from __future__ import annotations

import logging
import os
import socket
import time
from collections import defaultdict, deque

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


logger = logging.getLogger("urban_data_explorer.api")

# Compteurs de monitoring en memoire (par instance). Pour un deploiement multi-replicas
# derriere un load-balancer, on centraliserait ces compteurs (Redis/Prometheus) ; ici on
# expose l'etat de l'instance courante, ce qui suffit a demontrer le monitoring (C1.4).
_METRICS: dict[str, object] = {
    "requests_total": 0,
    "errors_total": 0,
    "slow_total": 0,
    "rate_limited_total": 0,
    "latency_ms_sum": 0.0,
    "by_status": defaultdict(int),
}

RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "240"))          # requetes autorisees
RATE_WINDOW = int(os.getenv("API_RATE_WINDOW", "60"))         # par fenetre (secondes)
SLOW_REQUEST_MS = float(os.getenv("API_SLOW_REQUEST_MS", "750"))  # seuil de log "lent"

# Chemins jamais soumis au rate-limit (sondes d'orchestration / page d'accueil / statique).
RATE_LIMIT_EXEMPT_PREFIXES = ("/health", "/metrics", "/static", "/docs", "/openapi.json")


class RateLimiter:
    """Fenetre glissante en memoire, par adresse IP."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        hits = self._hits[client_id]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Rate-limiting + mesure du temps de traitement + log des requetes lentes."""

    def __init__(self, app, rate_limiter: RateLimiter) -> None:
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not path.startswith(RATE_LIMIT_EXEMPT_PREFIXES):
            client_ip = request.client.host if request.client else "unknown"
            if not self.rate_limiter.allow(client_ip):
                _METRICS["rate_limited_total"] += 1
                logger.warning("rate_limit_exceeded ip=%s path=%s", client_ip, path)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": f"Trop de requetes (max {RATE_LIMIT}/{RATE_WINDOW}s)."},
                    headers={"Retry-After": str(RATE_WINDOW)},
                )

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.1f}"

        _METRICS["requests_total"] += 1
        _METRICS["latency_ms_sum"] += elapsed_ms
        _METRICS["by_status"][str(response.status_code)] += 1
        if response.status_code >= 500:
            _METRICS["errors_total"] += 1
        if elapsed_ms >= SLOW_REQUEST_MS:
            _METRICS["slow_total"] += 1
            logger.warning("slow_request path=%s ms=%.1f status=%s", path, elapsed_ms, response.status_code)
        return response


def install_observability(app) -> None:
    app.add_middleware(ObservabilityMiddleware, rate_limiter=RateLimiter(RATE_LIMIT, RATE_WINDOW))


def metrics_snapshot() -> dict[str, object]:
    """Instantane des compteurs de monitoring de l'instance courante (C1.4)."""
    requests_total = int(_METRICS["requests_total"])
    latency_sum = float(_METRICS["latency_ms_sum"])
    return {
        "instance": socket.gethostname(),
        "requests_total": requests_total,
        "errors_total": int(_METRICS["errors_total"]),
        "slow_total": int(_METRICS["slow_total"]),
        "rate_limited_total": int(_METRICS["rate_limited_total"]),
        "avg_latency_ms": round(latency_sum / requests_total, 2) if requests_total else 0.0,
        "by_status": dict(_METRICS["by_status"]),
    }


def security_status() -> dict[str, object]:
    """Etat de la securite, expose par /health pour la demo."""
    return {
        "rate_limit_per_window": RATE_LIMIT,
        "rate_window_seconds": RATE_WINDOW,
        "slow_request_threshold_ms": SLOW_REQUEST_MS,
    }
