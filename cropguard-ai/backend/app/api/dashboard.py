from fastapi import APIRouter, Depends, HTTPException

from app.services.mongo_client import DatabaseError, db_select
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(user: dict = Depends(get_current_user)):
    try:
        fields = await db_select("fields", {"user_id": f"eq.{user['id']}", "select": "*"})
        alerts = await db_select(
            "alerts", {"user_id": f"eq.{user['id']}", "order": "created_at.desc", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))

    return {
        "stats": {
            "total_fields": len(fields),
            "healthy_fields": len([f for f in fields if f["health_status"] == "healthy"]),
            "at_risk_fields": len([f for f in fields if f["health_status"] != "healthy"]),
            "active_alerts": len([a for a in alerts if not a["read"]]),
        },
        "fields": fields,
        "recent_alerts": alerts[:5],
    }
