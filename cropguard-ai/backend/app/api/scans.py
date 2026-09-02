from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.schemas.scans import HistoryPoint, ScanOut
from app.services import ai_service
from app.services.mongo_client import DatabaseError, db_insert, db_select, db_update
from app.services.recommendation_service import get_recommendation
from app.services.risk_service import compute_risk
from app.services.storage_service import StorageError, upload_scan_image
from app.services.weather_service import get_weather
from app.utils.auth import get_current_user
from app.utils.validation import validate_image_upload

router = APIRouter(prefix="/api", tags=["scans"])


def _row_to_scan(row: dict) -> ScanOut:
    return ScanOut(
        id=row["id"],
        field_id=row["field_id"],
        image_url=row["image_url"],
        timestamp=row["timestamp"],
        crop=row["crop"],
        is_demo=row["is_demo"],
        detections=row["detections"],
        severity=row["severity"],
        risk=row["risk"],
        weather=row.get("weather"),
        recommendation=row["recommendation"],
    )


@router.post("/analyze", response_model=ScanOut)
async def analyze_crop(
    field_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    # 1. Look up the field (also enforces it belongs to this user).
    try:
        field_rows = await db_select(
            "fields", {"id": f"eq.{field_id}", "user_id": f"eq.{user['id']}", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    if not field_rows:
        raise HTTPException(404, "Field not found.")
    field = field_rows[0]

    # 2. Validate + read the upload.
    image_bytes = await validate_image_upload(file)

    # 3. Run the AI pipeline (preprocessing -> detection -> severity).
    try:
        detection_result = await ai_service.analyze_image(image_bytes, crop=field["crop"])
    except ValueError as e:
        raise HTTPException(400, str(e))

    top_detection = detection_result.detections[0] if detection_result.detections else None

    # 4. Weather (feeds the risk model + is shown on the result screen).
    weather = await get_weather(field["latitude"], field["longitude"])

    # 5. Recent history, to flag a worsening trend.
    try:
        recent_scans = await db_select(
            "scans",
            {"field_id": f"eq.{field_id}", "order": "timestamp.desc", "limit": "3", "select": "severity"},
        )
    except DatabaseError:
        recent_scans = []
    trend_worsening = len(recent_scans) >= 2 and (
        recent_scans[0]["severity"]["affected_area_percent"]
        > recent_scans[-1]["severity"]["affected_area_percent"]
    )

    # 6. Risk model (explainable fusion of detection + weather + history).
    risk = compute_risk(
        detection_confidence=top_detection.confidence if top_detection else None,
        affected_area_percent=detection_result.severity.affected_area_percent,
        humidity_percent=weather.humidity_percent,
        recent_trend_worsening=trend_worsening,
    )

    # 7. Recommendation (template-based — see recommendation_service.py).
    recommendation = get_recommendation(
        top_detection.class_ if top_detection else None,
        top_detection.confidence if top_detection else None,
    )

    now = datetime.now(timezone.utc).isoformat()
    scan_id = str(uuid4())

    # 8. Upload the image to Supabase Storage before persisting the row, so
    #    the row's image_url always points at something real.
    try:
        image_url = await upload_scan_image(
            user_id=user["id"],
            field_id=field_id,
            scan_id=scan_id,
            content=image_bytes,
            content_type=file.content_type,
        )
    except StorageError as e:
        raise HTTPException(502, f"Analysis succeeded but the image couldn't be saved: {e}")

    # 9. Persist the scan.
    try:
        scan_row = await db_insert(
            "scans",
            {
                "id": scan_id,
                "field_id": field_id,
                "user_id": user["id"],
                "image_url": image_url,
                "timestamp": now,
                "crop": detection_result.crop,
                "is_demo": detection_result.is_demo,
                "detections": [d.model_dump(by_alias=True) for d in detection_result.detections],
                "severity": detection_result.severity.model_dump(),
                "risk": risk.model_dump(),
                "weather": weather.model_dump(),
                "recommendation": recommendation.model_dump(),
            },
        )

        # 10. Update the field's rollup status.
        await db_update(
            "fields",
            {"id": field_id},
            {
                "health_status": risk.level,
                "last_scan_at": now,
                "last_disease": top_detection.label if top_detection else None,
                "last_risk": risk.level,
            },
        )

        # 11. Auto-generate an alert on high risk.
        if risk.level == "high":
            await db_insert(
                "alerts",
                {
                    "user_id": user["id"],
                    "field_id": field_id,
                    "message": f"High disease risk detected in {field['name']}.",
                    "severity": "high",
                    "read": False,
                },
            )
    except DatabaseError as e:
        raise HTTPException(e.status_code, f"Scan completed but couldn't be saved: {e}")

    return _row_to_scan(scan_row)


@router.get("/scans", response_model=list[ScanOut])
async def list_scans(field_id: str | None = None, user: dict = Depends(get_current_user)):
    params = {"user_id": f"eq.{user['id']}", "order": "timestamp.desc", "select": "*"}
    if field_id:
        params["field_id"] = f"eq.{field_id}"
    try:
        rows = await db_select("scans", params)
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    return [_row_to_scan(r) for r in rows]


@router.get("/scans/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: str, user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "scans", {"id": f"eq.{scan_id}", "user_id": f"eq.{user['id']}", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    if not rows:
        raise HTTPException(404, "Scan not found. It may have expired.")
    return _row_to_scan(rows[0])


@router.get("/risk/{field_id}")
async def get_field_risk(field_id: str, user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "scans",
            {"field_id": f"eq.{field_id}", "user_id": f"eq.{user['id']}", "order": "timestamp.desc", "limit": "1"},
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    if not rows:
        raise HTTPException(404, "No scans yet for this field.")
    return rows[0]["risk"]


@router.get("/weather/current")
async def get_current_location_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    user: dict = Depends(get_current_user),
):
    weather = await get_weather(latitude, longitude)
    return weather.model_dump()


@router.get("/weather/{field_id}")
async def get_field_weather(field_id: str, user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "fields", {"id": f"eq.{field_id}", "user_id": f"eq.{user['id']}", "select": "*"}
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    if not rows:
        raise HTTPException(404, "Field not found.")
    field = rows[0]
    weather = await get_weather(field["latitude"], field["longitude"])
    return weather.model_dump()


@router.get("/fields/{field_id}/history", response_model=list[HistoryPoint])
async def get_field_history(field_id: str, user: dict = Depends(get_current_user)):
    try:
        rows = await db_select(
            "scans",
            {
                "field_id": f"eq.{field_id}",
                "user_id": f"eq.{user['id']}",
                "order": "timestamp.asc",
                "select": "timestamp,severity,risk",
            },
        )
    except DatabaseError as e:
        raise HTTPException(e.status_code, str(e))
    return [
        HistoryPoint(
            date=r["timestamp"][:10],
            affected_area_percent=r["severity"]["affected_area_percent"],
            severity=r["severity"]["level"],
            risk=r["risk"]["level"],
        )
        for r in rows
    ]
