"""
FastAPI router for flight alert CRUD operations.
"""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from database import create_alert, get_alerts_for_email, delete_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class CreateAlertRequest(BaseModel):
    email: str
    origin: str
    destination: str
    filters: dict   # full search params snapshot


class AlertResponse(BaseModel):
    id: str
    email: str
    origin: str
    destination: str
    filters: dict
    created_at: str
    last_run_at: Optional[str] = None


@router.post("", status_code=201)
async def create_new_alert(req: CreateAlertRequest):
    """Save a new flight alert."""
    import json
    alert_id = str(uuid.uuid4())
    create_alert(
        alert_id=alert_id,
        email=req.email,
        origin=req.origin,
        destination=req.destination,
        filters=req.filters,
    )
    return {
        "id": alert_id,
        "message": f"Alert created. You'll receive an email at {req.email} when matching flights are found.",
    }


@router.get("")
async def list_alerts(email: str):
    """List all alerts for an email address."""
    import json
    alerts = get_alerts_for_email(email)
    result = []
    for a in alerts:
        result.append({
            "id": a["id"],
            "email": a["email"],
            "origin": a["origin"],
            "destination": a["destination"],
            "filters": json.loads(a["filters"]),
            "created_at": a["created_at"],
            "last_run_at": a.get("last_run_at"),
        })
    return {"alerts": result}


@router.delete("/{alert_id}")
async def remove_alert(alert_id: str):
    """Delete an alert by ID."""
    delete_alert(alert_id)
    return {"message": "Alert deleted."}


@router.post("/{alert_id}/test")
async def test_alert(alert_id: str):
    """Manually trigger a check for a specific alert (for testing)."""
    from database import get_all_alerts
    from amadeus_client import AmadeusClient, AmadeusAuthError
    from scheduler import process_alert

    alerts = get_all_alerts()
    alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    try:
        client = AmadeusClient()
    except AmadeusAuthError as e:
        raise HTTPException(status_code=503, detail=str(e))

    await process_alert(client, alert)
    return {"message": "Alert check triggered. Check your email."}
