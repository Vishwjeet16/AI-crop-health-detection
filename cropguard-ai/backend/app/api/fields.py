from fastapi import APIRouter, Depends, HTTPException

from app.schemas.fields import FieldCreate, FieldOut
from app.services.mongo_client import DatabaseError, db_insert, db_select
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/fields", tags=["fields"])


def _row_to_field(row: dict) -> FieldOut:
    return FieldOut(
        id=row["id"],
        name=row["name"],
        crop=row["crop"],
        area_acres=row["area"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        health_status=row["health_status"],
        last_scan_at=row.get("last_scan_at"),
        last_disease=row.get("last_disease"),
        last_risk=row.get("last_risk"),
    )


@router.get("", response_model=list[FieldOut])
async def list_fields(user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "fields", {"user_id": f"eq.{user['id']}", "order": "created_at.desc", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    return [_row_to_field(r) for r in rows]


@router.get("/{field_id}", response_model=FieldOut)
async def get_field(field_id: str, user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "fields", {"id": f"eq.{field_id}", "user_id": f"eq.{user['id']}", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    if not rows:
        raise HTTPException(404, "Field not found.")
    return _row_to_field(rows[0])


@router.post("", response_model=FieldOut)
async def create_field(payload: FieldCreate, user: dict = Depends(get_current_user)):
    try:
        row = await db_insert(
            "fields",
            {
                "user_id": user["id"],
                "name": payload.name,
                "crop": payload.crop,
                "area": payload.area_acres,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "health_status": "healthy",
            },
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    return _row_to_field(row)
