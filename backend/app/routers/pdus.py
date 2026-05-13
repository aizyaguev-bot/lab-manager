import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Device
from ..schemas import PduStatus, OutletState, PowerAction
from ..routers.devices import get_creds
from drivers.raritan_pdu import RaritanPduDriver, RaritanPduError

router = APIRouter(prefix="/api/pdus", tags=["pdus"])


async def _get_pdu_or_404(device_id: str, db: AsyncSession) -> Device:
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.kind == "pdu")
    )
    dev = result.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="PDU not found")
    return dev


@router.get("/{device_id}/status", response_model=PduStatus)
async def pdu_status(device_id: str, db: AsyncSession = Depends(get_db)):
    dev = await _get_pdu_or_404(device_id, db)
    username, password = get_creds(dev)
    driver = RaritanPduDriver(dev.ip, username, password)
    try:
        outlets_raw = await driver.get_outlets()
        inlet = await driver.get_inlet()
        labels = json.loads(dev.labels_json or "{}")
        for o in outlets_raw:
            key = str(o["number"])
            # Only apply DB label when firmware has no custom name (default "Outlet N")
            if key in labels and o["label"] == f"Outlet {o['number']}":
                o["label"] = labels[key]
        outlets = [OutletState(**o) for o in outlets_raw]
        total_watts = sum(o.watts for o in outlets)
        return PduStatus(
            device_id=device_id,
            reachable=True,
            inlet_voltage=inlet.get("voltage", 0.0),
            total_watts=total_watts,
            outlets=outlets,
        )
    except RaritanPduError as e:
        return PduStatus(device_id=device_id, reachable=False, error=str(e))
    finally:
        await driver.close()


@router.post("/{device_id}/outlets/{outlet_number}/power")
async def outlet_power(
    device_id: str,
    outlet_number: int,
    body: PowerAction,
    db: AsyncSession = Depends(get_db),
):
    dev = await _get_pdu_or_404(device_id, db)
    username, password = get_creds(dev)
    driver = RaritanPduDriver(dev.ip, username, password)
    try:
        success = await driver.set_outlet_state(outlet_number, body.action)
        return {"ok": success, "outlet": outlet_number, "action": body.action}
    except (RaritanPduError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        await driver.close()
