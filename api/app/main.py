from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import router as auth_router, require_auth
from .routes.dashboard import router as dashboard_router
from .routes.health import router as health_router
from .routes.sources import router as sources_router
from .security import install_observability


def create_app() -> FastAPI:
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    app = FastAPI(
        title="Urban Data Explorer API",
        version="0.1.0",
        description="API et frontend statique pour explorer les dynamiques du logement parisien.",
    )
    install_observability(app)
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    # /health et /auth/token restent ouverts (sondes d'orchestration + login).
    # Les endpoints de donnees sont proteges par JWT (OAuth2) OU cle API quand une
    # securite est configuree (sinon ouverts, local-first).
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(sources_router, dependencies=[Depends(require_auth)])
    app.include_router(dashboard_router, dependencies=[Depends(require_auth)])

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    return app


app = create_app()
