"""
Raritan Dominion KVM driver.

KX III: REST API at https://<ip>/api/v1/ — returns port list and status.
        HTML5 viewer URL: https://<ip>/dom_kvm/connect?port=<n>&token=<session>

LX II:  Minimal REST; live iframe not supported. We return a direct HTTPS
        deep-link that opens the native viewer in a new browser tab.

SSL verification disabled for lab self-signed certs.
"""

import httpx
import hashlib
import time
from typing import Optional

TIMEOUT = 10.0


class RaritanKvmError(Exception):
    pass


class RaritanKvmDriver:
    def __init__(self, ip: str, username: str, password: str, model: str = "KX III"):
        self.ip = ip
        self.base_url = f"https://{ip}"
        self.username = username
        self.password = password
        self.model = model  # "KX III" | "LX II"
        self._session_token: Optional[str] = None
        self._client: httpx.AsyncClient | None = None

    async def _client_ctx(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=(self.username, self.password),
                verify=False,
                timeout=TIMEOUT,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def ping(self) -> bool:
        try:
            client = await self._client_ctx()
            resp = await client.get(f"{self.base_url}/api/v1/targets")
            return resp.status_code in (200, 401, 403)
        except Exception:
            return False

    async def get_ports(self) -> list[dict]:
        """Returns list of { number, label, status } for all KVM ports."""
        if "LX" in self.model:
            return await self._get_ports_lx()
        return await self._get_ports_kx()

    async def _get_ports_kx(self) -> list[dict]:
        """KX III: REST API at /api/v1/targets"""
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{self.base_url}/api/v1/targets")
            resp.raise_for_status()
            data = resp.json()
            targets = data if isinstance(data, list) else data.get("targets", data.get("list", []))
            ports = []
            for i, t in enumerate(targets):
                label = t.get("name", t.get("label", t.get("targetName", f"Port {i+1}")))
                raw_status = t.get("connectionStatus", t.get("status", t.get("state", "idle")))
                status = _parse_kvm_status(raw_status)
                ports.append({"number": i + 1, "label": label, "status": status})
            return ports
        except httpx.HTTPStatusError as e:
            raise RaritanKvmError(f"HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise RaritanKvmError(f"Connection error: {e}")

    async def _get_ports_lx(self) -> list[dict]:
        """LX II: tries /api/v1/targets, falls back to empty list."""
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{self.base_url}/api/v1/targets")
            if resp.status_code == 200:
                data = resp.json()
                targets = data if isinstance(data, list) else data.get("targets", [])
                return [
                    {
                        "number": i + 1,
                        "label": t.get("name", t.get("label", f"Port {i+1}")),
                        "status": _parse_kvm_status(t.get("status", "idle")),
                    }
                    for i, t in enumerate(targets)
                ]
        except Exception:
            pass
        return []

    def get_viewer_url(self, port_number: int) -> dict:
        """
        Returns a dict with:
          embed_url: iframe-safe URL (KX III only; None for LX II)
          launch_url: URL to open the viewer in a new tab
          can_embed: True only for KX III
        """
        if "LX" in self.model:
            return {
                "embed_url": None,
                "launch_url": f"{self.base_url}/",
                "can_embed": False,
            }

        # KX III: build an authenticated deep-link.
        # A real deployment should use a session token from /api/v1/auth/login.
        # For the mockup/dev phase we generate a direct URL; the browser will
        # show a login prompt if the session isn't already active.
        viewer_url = f"{self.base_url}/dom_kvm/connect?port={port_number}"
        return {
            "embed_url": viewer_url,
            "launch_url": viewer_url,
            "can_embed": True,
        }

    async def get_session_token(self) -> Optional[str]:
        """
        Logs into the KVM and returns a session token for the viewer URL.
        KX III: POST /api/v1/auth/login  → { "token": "..." }
        """
        if "LX" in self.model:
            return None
        client = await self._client_ctx()
        try:
            resp = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": self.username, "password": self.password},
            )
            if resp.status_code == 200:
                token = resp.json().get("token")
                self._session_token = token
                return token
        except Exception:
            pass
        return None


def _parse_kvm_status(raw) -> str:
    if not raw:
        return "idle"
    s = str(raw).lower()
    if s in ("connected", "active", "in-use", "inuse", "1", "true"):
        return "active"
    if s in ("available", "idle", "ready", "0", "false"):
        return "idle"
    if s in ("empty", "none", "no-target", "notarget"):
        return "empty"
    return "idle"
