"""
Seed your real lab devices into the database.
Run once after first install:  python seed.py

Reads PDU_USERNAME / PDU_PASSWORD / KVM_USERNAME / KVM_PASSWORD from .env
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, AsyncSessionLocal
from app.models import Device
from app.crypto import encrypt
from app.config import get_settings

DEVICES = [
    # ---- PDUs ----
    dict(id="pdu-rack01", kind="pdu", name="PDU-Rack-01", model="Raritan PDU", ip="10.7.30.137", rack="Rack-01"),
    dict(id="pdu-rack02", kind="pdu", name="PDU-Rack-02", model="Raritan PDU", ip="10.7.30.136", rack="Rack-02"),
    dict(id="pdu-rack03", kind="pdu", name="PDU-Rack-03", model="Raritan PDU", ip="10.7.30.129", rack="Rack-03"),
    dict(id="pdu-rack04", kind="pdu", name="PDU-Rack-04", model="Raritan PDU", ip="10.7.30.93",  rack="Rack-04"),
    dict(id="pdu-rack05", kind="pdu", name="PDU-Rack-05", model="Raritan PDU", ip="10.7.30.141", rack="Rack-05"),
    dict(id="pdu-rack06", kind="pdu", name="PDU-Rack-06", model="Raritan PDU", ip="10.7.30.201", rack="Rack-06"),
    # ---- KVMs ----
    dict(id="kvm-unit1", kind="kvm", name="KVM-Unit-1", model="Raritan Dominion KX III", ip="10.7.30.49",  rack="Rack-01", port_count=16),
    dict(id="kvm-unit2", kind="kvm", name="KVM-Unit-2", model="Raritan Dominion KX III", ip="10.7.30.115", rack="Rack-06", port_count=8),
    dict(id="kvm-unit3", kind="kvm", name="KVM-Unit-3", model="Raritan Dominion LX II",  ip="10.7.30.53",  rack="Rack-05", port_count=8),
]


async def main():
    settings = get_settings()
    await init_db()

    pdu_user = settings.pdu_username
    pdu_pass = settings.pdu_password
    kvm_user = settings.kvm_username
    kvm_pass = settings.kvm_password

    async with AsyncSessionLocal() as db:
        for d in DEVICES:
            existing = await db.get(Device, d["id"])
            if existing:
                print(f"  skip (already exists): {d['name']}")
                continue

            is_pdu = d["kind"] == "pdu"
            dev = Device(
                id=d["id"],
                kind=d["kind"],
                name=d["name"],
                model=d.get("model", ""),
                ip=d["ip"],
                rack=d.get("rack", ""),
                port_count=d.get("port_count", 0),
                username_enc=encrypt(pdu_user if is_pdu else kvm_user),
                password_enc=encrypt(pdu_pass if is_pdu else kvm_pass),
            )
            db.add(dev)
            print(f"  added: {d['name']} ({d['ip']})")

        await db.commit()

    print("\nDone. All devices seeded.")


if __name__ == "__main__":
    asyncio.run(main())
