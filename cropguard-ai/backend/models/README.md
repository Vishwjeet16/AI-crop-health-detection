# Model weights

Place a trained YOLO weights file here as `cropguard-yolo.pt` and set
`AI_MODE=production` in `backend/.env` to switch `app/services/ai_service.py`
from demo mode to real inference (Stage 6).

Until a weights file exists here, production mode automatically falls back
to demo mode with a logged warning — see `_yolo_available()` in
`app/services/ai_service.py`.
