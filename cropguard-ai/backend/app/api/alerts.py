from fastapi import APIRouter, Depends, HTTPException

from app.schemas.alerts import AlertOut
from app.services.mongo_client import DatabaseError, db_select, db_update
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _row_to_alert(row: dict, field_name: str) -> AlertOut:
    return AlertOut(
        id=row["id"],
        field_id=row["field_id"],
        field_name=field_name,
        message=row["message"],
        severity=row["severity"],
        created_at=row["created_at"],
        read=row["read"],
    )


@router.get("", response_model=list[AlertOut])
async def list_alerts(user: dict = Depends(get_current_user)):
    try:
        alert_rows = await db_select(
            "alerts", {"user_id": f"eq.{user['id']}", "order": "created_at.desc", "select": "*"}
        )
        field_rows = await db_select(
            "fields", {"user_id": f"eq.{user['id']}", "select": "id,name"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))

    field_names = {f["id"]: f["name"] for f in field_rows}
    return [_row_to_alert(a, field_names.get(a["field_id"], "Field")) for a in alert_rows]


@router.patch("/{alert_id}/read", response_model=AlertOut)
async def mark_alert_read(alert_id: str, user: dict = Depends(get_current_user)):
    try:
        row = await db_update("alerts", {"id": alert_id, "user_id": user["id"]}, {"read": True})
        field_rows = await db_select("fields", {"id": f"eq.{row['field_id']}", "select": "name"})
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    field_name = field_rows[0]["name"] if field_rows else "Field"
    return _row_to_alert(row, field_name)
