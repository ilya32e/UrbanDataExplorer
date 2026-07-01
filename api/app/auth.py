"""Authentification JWT / OAuth2 de l'API (C2.1).

Unique mecanisme d'authentification : **OAuth2 password flow -> JWT Bearer**
(standard, visible dans le bouton "Authorize" de Swagger). `POST /auth/token`
avec username/password renvoie un JWT signe (HS256) ; les endpoints proteges
exigent ensuite l'en-tete `Authorization: Bearer <token>`.

Si le JWT n'est pas configure cote serveur, l'API reste ouverte (local-first).
Variables d'environnement :

    AUTH_SECRET_KEY            secret de signature JWT (active OAuth2/JWT si defini)
    AUTH_USERNAME             identifiant autorise
    AUTH_PASSWORD             mot de passe (clair, local-first)  OU
    AUTH_PASSWORD_SHA256      empreinte SHA-256 du mot de passe (recommande)
    AUTH_TOKEN_EXPIRE_MINUTES duree de validite du token (defaut 60)
"""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "").strip()
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "").strip()
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
AUTH_PASSWORD_SHA256 = os.getenv("AUTH_PASSWORD_SHA256", "").strip().lower()
AUTH_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))

# auto_error=False : on decide nous-memes du 401 (acces ouvert si JWT non configure).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def jwt_auth_enabled() -> bool:
    return bool(AUTH_SECRET_KEY and AUTH_USERNAME and (AUTH_PASSWORD or AUTH_PASSWORD_SHA256))


def _password_ok(password: str) -> bool:
    if AUTH_PASSWORD_SHA256:
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, AUTH_PASSWORD_SHA256)
    if AUTH_PASSWORD:
        return hmac.compare_digest(password, AUTH_PASSWORD)
    return False


def authenticate(username: str, password: str) -> bool:
    return bool(AUTH_USERNAME) and hmac.compare_digest(username, AUTH_USERNAME) and _password_ok(password)


def create_access_token(subject: str) -> tuple[str, int]:
    expire_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": now + timedelta(seconds=expire_seconds),
    }
    token = jwt.encode(payload, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)
    return token, expire_seconds


def _valid_jwt(token: str | None) -> bool:
    if not token or not AUTH_SECRET_KEY:
        return False
    try:
        jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        return True
    except jwt.PyJWTError:
        return False


def require_auth(token: str | None = Security(oauth2_scheme)) -> str | None:
    """Dependance FastAPI : exige un JWT Bearer valide.

    Local-first : si le JWT n'est pas configure cote serveur, l'acces reste ouvert.
    """
    if not jwt_auth_enabled():
        return None
    if _valid_jwt(token):
        return "jwt"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise (JWT Bearer via /auth/token).",
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_status() -> dict[str, object]:
    """Etat de l'authentification, expose par /health pour la demo."""
    return {
        "jwt_oauth2_enabled": jwt_auth_enabled(),
        "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


router = APIRouter(tags=["auth"])


@router.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, object]:
    """OAuth2 password flow : echange username/password contre un JWT Bearer."""
    if not jwt_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth2/JWT non configure (definir AUTH_SECRET_KEY, AUTH_USERNAME, AUTH_PASSWORD).",
        )
    if not authenticate(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in}
