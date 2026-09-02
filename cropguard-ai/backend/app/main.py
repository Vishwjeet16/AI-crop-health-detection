import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import alerts, assistant, auth, dashboard, fields, images, scans
from app.config import get_settings
from app.services.mongo_client import ensure_indexes, ping

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="CropGuard AI API",
    description="Early detection and management of crop damage and pest infestation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # Consistent {status, error} envelope for the frontend's ApiError class.
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    # Without this, FastAPI's default 422 body is {"detail": [{...}, ...]} — a
    # list, which the frontend's ApiError renders as "Request failed (422)"
    # instead of telling the user what was wrong with the form. Flattened into
    # the same envelope as every other error, naming the field.
    parts = []
    for err in exc.errors():
        # loc is like ("body", "language"); the first element is the location
        # type, which means nothing to a user.
        field = ".".join(str(p) for p in err.get("loc", ())[1:]) or "request"
        parts.append(f"{field}: {err.get('msg', 'invalid value')}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "error": "; ".join(parts) or "Invalid request."},
    )


@app.on_event("startup")
async def create_indexes():
    """MongoDB has no DDL, so the indexes the app relies on are created here.

    Deliberately non-fatal: a developer whose mongod isn't running should still
    get a server that boots and returns a clear 503 from /health and from each
    data route, rather than a process that refuses to start.
    """
    try:
        await ensure_indexes()
    except Exception as e:  # DatabaseError or any driver error — same handling.
        logging.getLogger("startup").warning(
            "Could not create MongoDB indexes (%s). The API will start, but data "
            "routes will fail until MongoDB at %s is reachable.",
            e, settings.mongodb_uri,
        )


@app.get("/")
async def root():
    return {
        "name": "CropGuard AI API",
        "ai_mode": settings.ai_mode,
        "status": "ok",
    }


@app.get("/health")
async def health():
    """Reports the database too, so "is it up?" has one honest answer.

    Returns 200 either way with an explicit `database` field: the process being
    alive and the data layer being usable are different facts, and a monitor
    that conflates them can't tell a crashed API from a stopped mongod.
    """
    database_up = await ping()
    return {
        "status": "ok" if database_up else "degraded",
        "database": "up" if database_up else "unreachable",
    }


app.include_router(auth.router)
app.include_router(fields.router)
app.include_router(scans.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(assistant.router)
app.include_router(images.router)
