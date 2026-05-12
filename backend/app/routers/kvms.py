from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Device
from ..schemas import KvmStatus, KvmPort
from ..routers.devices import get_creds
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
async def kvm_status(device_id: str, db: AsyncSession = Depends(get_db)):
    dev = await _get_kvm_or_404(device_id, db)
    username, password = get_creds(dev)
    driver = RaritanKvmDriver(dev.ip, username, password, model=dev.model)
    try:
        ports_raw = await driver.get_ports()
        ports = [KvmPort(**p) for p in ports_raw]
        return KvmStatus(device_id=device_id, reachable=True, ports=ports)
    except RaritanKvmError as e:
        return KvmStatus(device_id=device_id, reachable=False, error=str(e))
    finally:
        await driver.close()


@router.get("/{device_id}/ports/{port_number}/viewer")
async def kvm_viewer_url(
    device_id: str,
    port_number: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the viewer URL(s) for a KVM port.
    Frontend uses embed_url for the iframe, launch_url for the new-tab button.
    Also attempts to fetch a fresh session token for KX III.
    """
    dev = await _get_kvm_or_404(device_id, db)
    username, password = get_creds(dev)
    driver = RaritanKvmDriver(dev.ip, username, password, model=dev.model)

    viewer = driver.get_viewer_url(port_number)

    if viewer["can_embed"]:
        token = await driver.get_session_token()
        if token:
            viewer["embed_url"] = f"{viewer['embed_url']}&token={token}"
            viewer["launch_url"] = f"{viewer['launch_url']}&token={token}"

    await driver.close()
    return viewer
