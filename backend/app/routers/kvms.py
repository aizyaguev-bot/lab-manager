import json
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Device
from ..schemas import KvmStatus, KvmPort
from ..routers.devices import get_creds
from ..routers.kvm_proxy import ensure_session
from drivers.raritan_kvm import RaritanKvmDriver, RaritanKvmError

router = APIRouter(prefix="/api/kvms", tags=["kvms"])


async def _get_kvm_or_404(device_id: str, db: AsyncSession) -> Device:
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.kind == "kvm")
    )
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="KVM not found")
    return dev


@router.get("/{device_id}/status", response_model=KvmStatus)
async def kvm_status(
    device_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    dev = await _get_kvm_or_404(device_id, db)
    username, password = get_creds(dev)
    driver = RaritanKvmDriver(dev.ip, username, password, model=dev.model)
    try:
        reachable = await driver.ping()
        if not reachable:
            return KvmStatus(device_id=device_id, reachable=False, error="Cannot reach device")
        ports_raw = await driver.get_ports(port_count=dev.port_count)
        labels = json.loads(dev.labels_json or "{}")
        for p in ports_raw:
            key = str(p["number"])
            if key in labels:
                p["label"] = labels[key]
        ports = [KvmPort(**p) for p in ports_raw]
        # Warm up the proxy session in the background so console opens instantly
        background_tasks.add_task(ensure_session, device_id, dev)
        return KvmStatus(device_id=device_id, reachable=True, ports=ports)
    except Exception as e:
        return KvmStatus(device_id=device_id, reachable=False, error=str(e))
    finally:
        await driver.close()


@router.get("/{device_id}/ports/{port_number}/viewer")
async def kvm_viewer_url(
    device_id: str,
    port_number: int,
    db: AsyncSession = Depends(get_db),
):
    dev = await _get_kvm_or_404(device_id, db)
    proxy_url = f"/api/kvms/{device_id}/proxy/home.asp"
    launch_url = f"https://{dev.ip}/home.asp"
    return {"embed_url": proxy_url, "launch_url": launch_url, "can_embed": True}
