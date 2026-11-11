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


# Hash de relleno: si el usuario no existe se verifica igual, para que el tiempo no revele qué emails existen.
_DUMMY_HASH = bcrypt.hashpw(b"escudo-dummy-password", bcrypt.gensalt(rounds=10)).decode()


class LoginThrottle:
    """Límite de intentos de inicio de sesión (en memoria del proceso, protegido con un cerrojo).

    - Por par (email, IP): MAX_PER_PAIR intentos fallidos en WINDOW_S → 429. Al ir ligado a la IP, un tercero
      no puede bloquear la cuenta de otra persona desde su propia conexión (sin bloqueo dirigido de cuentas).
    - Por IP (IPv6 agrupado por /64): MAX_PER_IP intentos fallidos → 429 (frena probar muchos emails).
    - Por cuenta, global: MAX_PER_EMAIL intentos fallidos desde cualquier IP → 429 para conexiones NUEVAS
      (frena la fuerza bruta distribuida). No se aplica a las conexiones desde las que la cuenta entró bien en
      los últimos TRUST_S segundos, para que un ataque no impida entrar a la persona legítima.
    El intento se RESERVA de forma atómica antes de comprobar la contraseña (sin carreras entre peticiones
    simultáneas) y se libera si el acceso es correcto.
    """

    WINDOW_S, MAX_PER_PAIR, MAX_PER_IP, MAX_PER_EMAIL = 15 * 60, 10, 50, 100
    TRUST_S = 30 * 24 * 3600  # una conexión desde la que la cuenta entró bien es de confianza 30 días

    def __init__(self) -> None:
        import threading

        self._fails: dict[str, list[float]] = {}
        self._trusted: dict[str, dict[str, float]] = {}  # email → {grupo de IP: último acceso correcto}
        self._lock = threading.Lock()

    def _is_trusted(self, email: str, ip: str, now: float) -> bool:
        t = self._trusted.get(email, {}).get(self._ip_group(ip))
        return t is not None and now - t < self.TRUST_S

    def _recent(self, key: str, now: float) -> list[float]:
        xs = [t for t in self._fails.get(key, []) if now - t < self.WINDOW_S]
        if xs:
            self._fails[key] = xs
        else:
            self._fails.pop(key, None)
        return xs

    @staticmethod
    def _ip_group(ip: str) -> str:
        """IPv6 se agrupa por /64 (un usuario dispone de millones de direcciones dentro de su bloque)."""
        import ipaddress

        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            return ip
        if a.version == 6:
            if a.ipv4_mapped:  # ::ffff:1.2.3.4 → 1.2.3.4
                return str(a.ipv4_mapped)
            return str(ipaddress.ip_network(f"{a}/64", strict=False))
        return str(a)

    def _keys(self, email: str, ip: str) -> tuple[str, str, str]:
        g = self._ip_group(ip)
        return f"p:{email}|{g}", f"i:{g}", f"e:{email}"

    def reserve(self, email: str, ip: str, now: float) -> int | None:
        """Reserva un intento. Devuelve segundos de espera si se ha superado el límite (y no reserva)."""
        keys = self._keys(email, ip)
        limits = (self.MAX_PER_PAIR, self.MAX_PER_IP, self.MAX_PER_EMAIL)
        with self._lock:
            trusted = self._is_trusted(email, ip, now)
            for k, limit in zip(keys, limits, strict=True):
                if k.startswith("e:") and trusted:
                    continue  # sin bloqueo dirigido: la conexión habitual de la persona sigue pudiendo entrar
                xs = self._recent(k, now)
                if len(xs) >= limit:
                    return int(self.WINDOW_S - (now - xs[0])) + 1
            for k in keys:
                self._fails.setdefault(k, []).append(now)
            return None

    def release(self, email: str, ip: str, now: float) -> None:
        """Acceso correcto: se libera la reserva y se limpia el contador del par (email, IP)."""
        kp, ki, ke = self._keys(email, ip)
        with self._lock:
            self._trusted.setdefault(email, {})[self._ip_group(ip)] = now
            self._fails.pop(kp, None)
            for k in (ki, ke):
                xs = self._fails.get(k, [])
                if now in xs:
                    xs.remove(now)

    # Compatibilidad con pruebas antiguas
    def retry_after(self, email: str, ip: str, now: float) -> int | None:
        limits = (self.MAX_PER_PAIR, self.MAX_PER_IP, self.MAX_PER_EMAIL)
        with self._lock:
            for k, limit in zip(self._keys(email, ip), limits, strict=True):
                xs = self._recent(k, now)
                if len(xs) >= limit:
                    return int(self.WINDOW_S - (now - xs[0])) + 1
        return None

    def reset(self) -> None:
        with self._lock:
            self._fails.clear()
            self._trusted.clear()


login_throttle = LoginThrottle()


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
