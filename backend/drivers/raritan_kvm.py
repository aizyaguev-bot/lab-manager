"""
Raritan Dominion KVM driver.

Supports two device generations:
  KX III / KX IV: REST API at /api/v1/ (newer firmware).
                  Falls back to static port list on older firmware.
  LX II:          No REST API. Returns static port list + direct launch link.

SSL verification disabled for lab self-signed certs.
"""

import httpx
from typing import Optional

TIMEOUT = 6.0


class RaritanKvmError(Exception):
    pass


class RaritanKvmDriver:
    def __init__(self, ip: str, username: str, password: str, model: str = "KX III"):
        self.ip = ip
        self.base_url = f"https://{ip}"
        self.username = username
        self.password = password
        self.model = model
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
        """Returns True if the KVM is reachable (any HTTP response)."""
        try:
            client = await self._client_ctx()
            resp = await client.get(f"{self.base_url}/")
            return resp.status_code < 500
        except Exception:
            return False

    async def get_ports(self, port_count: int = 0) -> list[dict]:
        """
        Returns list of { number, label, status } for all KVM ports.
        Tries REST API first; falls back to static list based on port_count.
        """
        if "LX" not in self.model:
            try:
                return await self._get_ports_rest()
            except RaritanKvmError:
                pass
        # Fallback: return generic port list
        return [{"number": i + 1, "label": f"Port {i + 1}", "status": "idle"}
                for i in range(port_count)]

    async def _get_ports_rest(self) -> list[dict]:
        """KX III newer firmware: REST API at /api/v1/targets."""
        client = await self._client_ctx()
        resp = await client.get(f"{self.base_url}/api/v1/targets")
        if resp.status_code != 200:
            raise RaritanKvmError(f"HTTP {resp.status_code}")
        data = resp.json()
        targets = data if isinstance(data, list) else data.get("targets", data.get("list", []))
        ports = []
        for i, t in enumerate(targets):
            label = t.get("name", t.get("label", t.get("targetName", f"Port {i+1}")))
            raw_status = t.get("connectionStatus", t.get("status", t.get("state", "idle")))
            status = _parse_kvm_status(raw_status)
            ports.append({"number": i + 1, "label": label, "status": status})
        return ports

    def get_viewer_url(self, port_number: int) -> dict:
        """
        Returns { embed_url, launch_url, can_embed }.
        KX III / LX II: use the HTML5 viewer at /html5/ (requires one-time browser login).
        """
        base = self.base_url
        embed_url = f"{base}/html5/"
        launch_url = f"{base}/html5/"
        return {"embed_url": embed_url, "launch_url": launch_url, "can_embed": True}

    async def get_session_token(self) -> Optional[str]:
        """Logs in via REST API and returns a session token (KX III newer firmware only)."""
        client = await self._client_ctx()
        try:
            resp = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": self.username, "password": self.password},
            )
            if resp.status_code == 200:
                return resp.json().get("token")
        except Exception:
            pass
        return None


def _parse_kvm_status(raw) -> str:
    if not raw:
        return "idle"
    s = str(raw).lower().strip()
    if s in ("connected", "active", "in-use", "inuse", "1", "true"):
        return "active"
    if s in ("empty", "none", "no-target", "notarget", "0",
             "disconnected", "down", "not-connected", "not connected",
             "unavailable", "not available"):
        return "empty"
    return "idle"
