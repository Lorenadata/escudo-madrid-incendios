from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import Membership, User

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=settings.jwt_ttl_minutes)}
    return jwt.encode(payload, settings.escudo_jwt_secret, algorithm="HS256")


class Principal:
    def __init__(self, user: User):
        self.user = user
        self.memberships: list[Membership] = list(user.memberships)

    @property
    def org_ids(self) -> set[str]:
        return {m.organization_id for m in self.memberships}

    def require_org(self, organization_id: str) -> Membership:
        for m in self.memberships:
            if m.organization_id == organization_id:
                return m
        # 404 en lugar de 403 para no revelar existencia de recursos de otras organizaciones
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recurso no encontrado")

    @property
    def default_org_id(self) -> str:
        if not self.memberships:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "El usuario no pertenece a ninguna organización")
        return self.memberships[0].organization_id


def current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer), session: Session = Depends(get_session)
) -> Principal:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticación requerida")
    try:
        payload = jwt.decode(creds.credentials, settings.escudo_jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o caducado") from exc
    user = session.scalar(select(User).where(User.id == payload.get("sub"), User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido")
    return Principal(user)
