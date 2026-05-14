"""
KVM regression tests — baseline commit: c73e69e

Run on the VM (backend must be running on port 8000, KVMs must be reachable):

    cd /opt/lab-manager/backend
    python -m pytest tests/test_kvm_regression.py -v

If LAB_MANAGER_PASSWORD is set in the environment, tests authenticate automatically.
"""

import os
import re
import requests
import pytest

BASE_URL = "http://localhost:8000"
_pw = os.getenv("LAB_MANAGER_PASSWORD", "")
AUTH = ("", _pw) if _pw else None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def kvm_devices():
    r = requests.get(f"{BASE_URL}/api/devices", auth=AUTH, timeout=10)
    assert r.status_code == 200, f"Cannot reach backend: {r.status_code} — is it running?"
    kvms = [d for d in r.json() if d["kind"] == "kvm"]
    assert kvms, "No KVM devices found in the database — add devices first"
    return kvms


@pytest.fixture(scope="module")
def reachable_kvms(kvm_devices):
    result = []
    for kvm in kvm_devices:
        r = requests.get(f"{BASE_URL}/api/kvms/{kvm['id']}/status", auth=AUTH, timeout=15)
        if r.status_code == 200 and r.json().get("reachable"):
            result.append(kvm)
    assert result, "No KVM devices are reachable — check network/credentials"
    return result


# ---------------------------------------------------------------------------
# Basic connectivity
# ---------------------------------------------------------------------------

def test_backend_version_endpoint():
    """Backend exposes a /api/version endpoint returning the git hash."""
    r = requests.get(f"{BASE_URL}/api/version", auth=AUTH, timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert data["version"] not in ("", None)
    print(f"\n  deployed commit: {data['version']}")


def test_kvm_devices_registered(kvm_devices):
    """At least one KVM is registered in the database."""
    assert len(kvm_devices) >= 1
    print(f"\n  KVMs: {[k['name'] for k in kvm_devices]}")


def test_kvm_status_reachable(reachable_kvms):
    """Each reachable KVM returns a valid status response."""
    for kvm in reachable_kvms:
        r = requests.get(f"{BASE_URL}/api/kvms/{kvm['id']}/status", auth=AUTH, timeout=15)
        assert r.status_code == 200, f"{kvm['name']}: status returned {r.status_code}"
        data = r.json()
        assert data["reachable"], f"{kvm['name']}: marked unreachable"
        assert isinstance(data.get("ports"), list), f"{kvm['name']}: no ports list"
        print(f"\n  {kvm['name']}: {len(data['ports'])} ports")


# ---------------------------------------------------------------------------
# Autologin — core regression (baseline c73e69e)
# ---------------------------------------------------------------------------

def test_autologin_returns_html(reachable_kvms):
    """Autologin endpoint returns 200 HTML for every reachable KVM."""
    for kvm in reachable_kvms:
        r = requests.get(
            f"{BASE_URL}/api/kvms/{kvm['id']}/autologin?port=1",
            auth=AUTH, timeout=20,
        )
        assert r.status_code == 200, f"{kvm['name']}: autologin returned {r.status_code}"
        assert "text/html" in r.headers.get("content-type", ""), \
            f"{kvm['name']}: response is not HTML"


def test_autologin_contains_session_id(reachable_kvms):
    """
    REGRESSION: autologin HTML must contain sessionId= in the jsclient URL.

    Without sessionId, jsclient shows: 0x10000003 Authentication failed.
    Fixed in commit c73e69e by fetching SESSION_ID from sidebar.asp.
    """
    for kvm in reachable_kvms:
        r = requests.get(
            f"{BASE_URL}/api/kvms/{kvm['id']}/autologin?port=1",
            auth=AUTH, timeout=20,
        )
        assert r.status_code == 200
        html = r.text

        assert "sessionId=" in html, (
            f"{kvm['name']}: sessionId missing from autologin HTML — "
            "jsclient will show 'Authentication failed' without it"
        )

        m = re.search(r"sessionId=([0-9a-fA-F]+)", html)
        assert m, f"{kvm['name']}: sessionId= found but no hex value follows it"
        sid = m.group(1)
        assert len(sid) >= 20, (
            f"{kvm['name']}: sessionId '{sid}' is too short ({len(sid)} chars) — "
            "expected 40+ hex chars from sidebar.asp SESSION_ID"
        )
        print(f"\n  {kvm['name']}: sessionId={sid[:12]}… ({len(sid)} chars)")


def test_autologin_direct_to_kvm_not_proxy(reachable_kvms):
    """
    Autologin must navigate the browser DIRECTLY to the KVM's jsclient URL,
    not through our backend proxy path (/api/kvms/.../proxy/...).

    The proxy approach is broken because it can't handle all KVM WebSocket auth.
    """
    for kvm in reachable_kvms:
        r = requests.get(
            f"{BASE_URL}/api/kvms/{kvm['id']}/autologin?port=1",
            auth=AUTH, timeout=20,
        )
        html = r.text
        kvm_ip = kvm["ip"]

        assert f"https://{kvm_ip}/jsclient/Client.asp" in html, (
            f"{kvm['name']}: autologin should point directly to "
            f"https://{kvm_ip}/jsclient/Client.asp, not through proxy"
        )
        assert "/proxy/jsclient" not in html, (
            f"{kvm['name']}: autologin is incorrectly routing through the proxy"
        )


def test_autologin_contains_port_number(reachable_kvms):
    """Autologin URL must include portNo= for the requested port."""
    for kvm in reachable_kvms:
        for port in [1, 2]:
            r = requests.get(
                f"{BASE_URL}/api/kvms/{kvm['id']}/autologin?port={port}",
                auth=AUTH, timeout=20,
            )
            assert r.status_code == 200
            assert f"portNo={port}" in r.text, \
                f"{kvm['name']}: portNo={port} missing from autologin HTML"


def test_autologin_has_cert_probe(reachable_kvms):
    """Autologin page must include a TLS cert probe (fetch no-cors) for UX."""
    for kvm in reachable_kvms:
        r = requests.get(
            f"{BASE_URL}/api/kvms/{kvm['id']}/autologin?port=1",
            auth=AUTH, timeout=20,
        )
        html = r.text
        assert 'no-cors' in html, \
            f"{kvm['name']}: cert probe (fetch no-cors) missing from autologin page"


# ---------------------------------------------------------------------------
# In-use tracking
# ---------------------------------------------------------------------------

def test_mark_in_use(reachable_kvms):
    """mark-in-use endpoint returns 200."""
    kvm = reachable_kvms[0]
    r = requests.post(
        f"{BASE_URL}/api/kvms/{kvm['id']}/ports/1/mark-in-use",
        auth=AUTH, timeout=10,
    )
    assert r.status_code == 200
    assert r.json().get("ok") is True
