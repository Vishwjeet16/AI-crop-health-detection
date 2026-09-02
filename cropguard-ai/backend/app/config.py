from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # --- MongoDB (app/services/mongo_client.py) -----------------------------
    # Holds all application data: users, fields, scans, alerts, weather.
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "cropguard"
    # Kept short on purpose: a stopped mongod should surface as a fast, clear
    # 503 rather than a request that hangs for the driver's 30s default.
    mongodb_timeout_ms: int = 5000

    # This server's own externally-reachable base URL. Only used to build the
    # absolute image_url returned by app/services/storage_service.py: next/image
    # resolves a relative path against the frontend's origin, not the API's, so
    # a relative one would 404 in the browser. Change this when the API is not
    # on localhost:8000.
    api_base_url: str = "http://localhost:8000"

    # "demo" returns simulated AI results; "production" calls the trained
    # YOLO model once it's wired in Stage 6. See app/services/ai_service.py.
    ai_mode: str = "demo"

    weather_api_key: str = ""

    # --- AI assistant (app/services/assistant_service.py) -------------------
    # Left empty by default: with no key the /api/assistant/chat route returns
    # a 503 explaining what to set, and every other feature keeps working.
    anthropic_api_key: str = ""
    assistant_model: str = "claude-opus-5"
    # Opus 5 thinks by default and max_tokens covers thinking + visible text
    # together, so this has to leave room for both.
    assistant_max_tokens: int = 4096
    # low/medium are strong on this model and are the main latency lever, which
    # matters for a chat box a farmer is waiting on.
    assistant_effort: str = "low"
    # Turns kept from the client's history. Caps prompt size and cost.
    assistant_history_turns: int = 8

    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:3000"

    max_upload_mb: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
