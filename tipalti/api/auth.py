"""OAuth2 client-credentials acquisition with on-disk token cache.

Cache file: ``$XDG_CACHE_HOME/tipalti/token-<env>.json`` (fallback
``$HOME/.cache/tipalti/...``), file mode ``0600``. The cache record includes
a short hash of the client ID; rotating credentials invalidates the cache.

Refresh window: tokens are refreshed when their remaining lifetime is less
than :data:`REFRESH_WINDOW_SECONDS`.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from tipalti.api._env import TipaltiEnv
from tipalti.api.errors import from_http_response, from_transport_error
from tipalti.cli._errors import EXIT_USER_ERROR, AfiError

REFRESH_WINDOW_SECONDS = 30
_TOKEN_REQUEST_TIMEOUT = 15.0


@dataclass(frozen=True)
class CachedToken:
    access_token: str
    expires_at: int
    env: str
    client_id_hash: str

    def is_fresh(self, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        return self.expires_at - ts > REFRESH_WINDOW_SECONDS


def _client_id_hash(client_id: str) -> str:
    return hashlib.sha256(client_id.encode("utf-8")).hexdigest()[:16]


def _cache_root() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "tipalti"


def cache_path(env: str) -> Path:
    return _cache_root() / f"token-{env}.json"


def read_cached(env: TipaltiEnv) -> CachedToken | None:
    """Return a fresh cached token, or ``None`` if missing/stale/mismatched."""
    path = cache_path(env.env)
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    try:
        token = CachedToken(
            access_token=str(data["access_token"]),
            expires_at=int(data["expires_at"]),
            env=str(data["env"]),
            client_id_hash=str(data["client_id_hash"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
    if token.env != env.env:
        return None
    if token.client_id_hash != _client_id_hash(env.client_id):
        return None
    if not token.is_fresh():
        return None
    return token


def write_cache(env: TipaltiEnv, token: CachedToken) -> None:
    """Atomically write the token cache via a same-directory tempfile.

    A symlink at the final path can't redirect the truncating write because
    we open and write through ``mkstemp`` (which creates a fresh inode in
    the same directory), then ``os.replace`` into place.
    """
    path = cache_path(env.env)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "access_token": token.access_token,
        "expires_at": token.expires_at,
        "env": token.env,
        "client_id_hash": token.client_id_hash,
    }
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def fetch_token(env: TipaltiEnv, *, transport: httpx.BaseTransport | None = None) -> CachedToken:
    """Hit the OAuth2 token endpoint and return a fresh :class:`CachedToken`."""
    data = {
        "grant_type": "client_credentials",
        "client_id": env.client_id,
        "client_secret": env.client_secret,
    }
    try:
        with httpx.Client(transport=transport, timeout=_TOKEN_REQUEST_TIMEOUT) as client:
            response = client.post(
                env.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise from_transport_error(exc) from exc

    if response.status_code >= 400:
        raise from_http_response(response)

    try:
        body = response.json()
    except (ValueError, json.JSONDecodeError):
        body = None

    access_token: str = ""
    expires_in: int = 0
    if isinstance(body, dict):
        token_value = body.get("access_token")
        if isinstance(token_value, str):
            access_token = token_value
        raw_expires = body.get("expires_in")
        if isinstance(raw_expires, (int, float)):
            expires_in = int(raw_expires)
        elif isinstance(raw_expires, str):
            try:
                expires_in = int(float(raw_expires))
            except ValueError:
                expires_in = 0

    if not access_token or expires_in <= 0:
        snippet = response.text[:200].replace("\n", " ").strip()
        raise AfiError(
            code=EXIT_USER_ERROR,
            message=(
                f"invalid token response from {env.token_url} "
                f"(status {response.status_code}): {snippet}"
            ),
            remediation="check TIPALTI_CLIENT_ID/SECRET and TIPALTI_TOKEN_URL",
        )

    return CachedToken(
        access_token=access_token,
        expires_at=int(time.time()) + expires_in,
        env=env.env,
        client_id_hash=_client_id_hash(env.client_id),
    )


def get_token(env: TipaltiEnv, *, transport: httpx.BaseTransport | None = None) -> CachedToken:
    """Return a fresh token, using the on-disk cache when valid."""
    cached = read_cached(env)
    if cached is not None:
        return cached
    token = fetch_token(env, transport=transport)
    try:
        write_cache(env, token)
    except OSError:
        # Cache is a perf optimization; a write failure shouldn't kill the call.
        pass
    return token
