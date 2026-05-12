"""
Raritan PX series PDU driver — JSON-RPC over HTTPS with Basic auth.

Tested against PX4. Falls back gracefully on older firmware.
SSL verification is disabled (lab self-signed certs).
"""

import httpx
import json
import asyncio
from typing import Any

TIMEOUT = 10.0


class RaritanPduError(Exception):
    pass


class RaritanPduDriver:
    def __init__(self, ip: str, username: str, password: str):
        self.base_url = f"https://{ip}"
        self.auth = (username, password)
        self._client: httpx.AsyncClient | None = None

    async def _client_ctx(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=self.auth,
                verify=False,
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _rpc(self, method: str, params: Any = None, rid: int = 1) -> Any:
        """Single JSON-RPC call via the /bulk endpoint."""
        client = await self._client_ctx()
        payload = {
            "requests": [
                {
                    "rid": str(rid),
                    "json": json.dumps({
                        "jsonrpc": "2.0",
                        "id": rid,
                        "method": method,
                        "params": params or {},
                    }),
                }
            ]
        }
        try:
            resp = await client.post(f"{self.base_url}/bulk", json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RaritanPduError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.RequestError as e:
            raise RaritanPduError(f"Connection error: {e}")

        data = resp.json()
        # /bulk returns {"responses": [{"rid": "1", "json": "<escaped json>"}]}
        responses = data.get("responses", [])
        if not responses:
            raise RaritanPduError("Empty response from PDU")
        inner = json.loads(responses[0]["json"])
        if "error" in inner:
            raise RaritanPduError(f"RPC error {inner['error'].get('code')}: {inner['error'].get('message')}")
        return inner.get("result")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Returns True if the PDU is reachable and auth works."""
        try:
            await self._rpc("getInlets")
            return True
        except RaritanPduError:
            return False
        except Exception:
            return False

    async def get_outlet_count(self) -> int:
        result = await self._rpc("getOutletCount")
        if isinstance(result, int):
            return result
        if isinstance(result, dict):
            return result.get("count", 24)
        return 24

    async def get_outlets(self) -> list[dict]:
        """
        Returns a list of outlet dicts:
          { number, label, state, watts, current, voltage }
        """
        # Try modern bulk outlet read
        try:
            result = await self._rpc("getOutlets")
            if isinstance(result, list):
                return [_parse_outlet(o, i + 1) for i, o in enumerate(result)]
        except RaritanPduError:
            pass

        # Fallback: read outlets one-by-one
        count = await self.get_outlet_count()
        tasks = [self._get_single_outlet(n) for n in range(1, count + 1)]
        return await asyncio.gather(*tasks)

    async def _get_single_outlet(self, number: int) -> dict:
        try:
            result = await self._rpc("getOutlet", {"outletId": number}, rid=number)
            return _parse_outlet(result, number)
        except RaritanPduError:
            return _empty_outlet(number)

    async def set_outlet_state(self, outlet_number: int, action: str) -> bool:
        """
        action: "on" | "off" | "cycle"
        Returns True on success.
        """
        action_map = {"on": 1, "off": 0, "cycle": 2}
        if action not in action_map:
            raise ValueError(f"Unknown action: {action}")

        # Try modern method first
        for method in ("switchOutlet", "setPowerState", "setOutletPowerState"):
            try:
                await self._rpc(method, {
                    "outletId": outlet_number,
                    "state": action_map[action],
                })
                return True
            except RaritanPduError as e:
                if "method not found" in str(e).lower() or "unknown method" in str(e).lower():
                    continue
                raise
        raise RaritanPduError("No working setPowerState method found on this firmware")

    async def get_inlet(self) -> dict:
        """Returns inlet voltage/current/power summary."""
        try:
            result = await self._rpc("getInlets")
            if isinstance(result, list) and result:
                inlet = result[0]
                return {
                    "voltage": _safe_float(inlet, "voltage", "rmsvoltage", "lineVoltage"),
                    "current": _safe_float(inlet, "current", "rmscurrent", "lineCurrent"),
                    "watts": _safe_float(inlet, "activePower", "power", "watts"),
                }
        except RaritanPduError:
            pass
        return {"voltage": 0.0, "current": 0.0, "watts": 0.0}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_outlet(data: dict, number: int) -> dict:
    if not isinstance(data, dict):
        return _empty_outlet(number)
    state_raw = data.get("powerState", data.get("state", data.get("status", 0)))
    # state_raw: 0=off, 1=on, 2=cycling; or string "on"/"off"
    if isinstance(state_raw, str):
        state = "on" if state_raw.lower() in ("on", "1", "true") else "off"
    else:
        state = "on" if state_raw == 1 else "off"

    watts = _safe_float(data, "activePower", "power", "watts", "wattage")
    current = _safe_float(data, "rmsCurrent", "current", "ampere")
    voltage = _safe_float(data, "rmsVoltage", "voltage", "volt")
    label = data.get("name", data.get("label", f"Outlet {number}")) or f"Outlet {number}"

    return {
        "number": number,
        "label": label,
        "state": state,
        "watts": round(watts, 1),
        "current": round(current, 2),
        "voltage": round(voltage, 1),
    }

def _empty_outlet(number: int) -> dict:
    return {"number": number, "label": f"Outlet {number}", "state": "unknown",
            "watts": 0.0, "current": 0.0, "voltage": 0.0}

def _safe_float(data: dict, *keys: str) -> float:
    for k in keys:
        v = data.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return 0.0
