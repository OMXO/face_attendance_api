import os
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.supabase_client import get_supabase
from api.schemas import RecognizeResponse
from api.embedding import get_embedding_from_image_bytes

# Routers
from api.routes.employees import router as employees_router
from api.routes.cameras import router as cameras_router
from api.routes.logs import router as logs_router
from api.routes.faces import router as faces_router

load_dotenv()

app = FastAPI(
    title="Face Attendance API",
    version="1.0.0",
)

# -----------------------------
# CORS
# -----------------------------
origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Routers mount (중요: app 생성 후 include_router)
# -----------------------------
app.include_router(cameras_router, prefix="/cameras", tags=["cameras"])
app.include_router(employees_router, prefix="/employees", tags=["employees"])
app.include_router(logs_router, prefix="/logs", tags=["logs"])
app.include_router(faces_router, tags=["faces"])  # /employees/{id}/faces 같은 형태면 prefix 불필요

# -----------------------------
# Helpers
# -----------------------------
def vec_to_pgvector_str(v: np.ndarray) -> str:
    v = v.astype(np.float32).tolist()
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# -----------------------------
# Basic endpoints
# -----------------------------
@app.get("/")
def root():
    return {
        "service": "Face Attendance API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "recognize": "/recognize",
        "cameras": "/cameras",
        "employees": "/employees",
        "logs": "/logs",
    }
    # return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    return {"ok": True}

# -----------------------------
# Recognize
# -----------------------------
@app.post("/recognize", response_model=RecognizeResponse)
async def recognize(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(default=None),
    event_type: Optional[str] = Form(default=None),
):
    """
    Streamlit(또는 클라이언트)에서 multipart/form-data로:
    - file: 이미지
    - camera_id: 카메라 식별자 (없으면 env CAMERA_ID fallback)
    - event_type: CHECK_IN / CHECK_OUT (없으면 env DEFAULT_EVENT_TYPE fallback)
    """

    # ---- 파일 검증 ----
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid content_type: {file.content_type}. Must be image/*")

    img_bytes = await file.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # ---- camera_id / event_type 결정 ----
    cam = (camera_id or "").strip() or os.getenv("CAMERA_ID", "").strip()
    if not cam:
        raise HTTPException(status_code=400, detail="camera_id is required (form field) or set CAMERA_ID env var")

    evt = (event_type or "").strip() or os.getenv("DEFAULT_EVENT_TYPE", "CHECK_IN")
    if evt not in ("CHECK_IN", "CHECK_OUT"):
        raise HTTPException(status_code=400, detail="event_type must be CHECK_IN or CHECK_OUT")

    min_sim = float(os.getenv("MIN_SIMILARITY", "0.45"))

    # ---- 임베딩 생성 (512,) ----
    try:
        emb = get_embedding_from_image_bytes(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    if not isinstance(emb, np.ndarray):
        raise HTTPException(status_code=500, detail="Embedding must be numpy.ndarray")
    emb = emb.reshape(-1)

    if emb.ndim != 1:
        raise HTTPException(status_code=500, detail="Embedding must be 1D vector")
    if emb.shape[0] != 512:
        raise HTTPException(status_code=500, detail=f"Embedding dim mismatch: got {emb.shape[0]}, expected 512")

    supabase = get_supabase()

    # ---- DB에서 Top-1 매칭 (RPC) ----
    query_vec = vec_to_pgvector_str(emb)

    try:
        match = supabase.rpc(
            "match_face",
            {"query_embedding": query_vec, "min_similarity": min_sim},
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase RPC failed: {str(e)}")

    # 등록자 0명 등
    if not match.data:
        # 인식 실패여도 로그 남기고 싶으면 아래처럼 employee_id=None으로 저장
        try:
            supabase.table("attendance_logs").insert({
                "employee_id": None,
                "camera_id": cam,
                "event_type": evt,
                "similarity": None,
                "recognized": False,
                "event_time": utc_now_iso(),
            }).execute()
        except Exception:
            pass

        return RecognizeResponse(employee_id=None, similarity=None, recognized=False)

    row = match.data[0]
    employee_id = row.get("employee_id")
    similarity = float(row.get("similarity", 0.0))
    recognized = bool(row.get("recognized", False))

    # ---- 출석 로그 기록 ----
    log_payload = {
        "employee_id": employee_id if recognized else None,
        "camera_id": cam,
        "event_type": evt,
        "similarity": similarity if recognized else similarity,  # 실패여도 similarity 남기고 싶으면 그대로
        "recognized": recognized,
        "event_time": utc_now_iso(),
    }

    try:
        supabase.table("attendance_logs").insert(log_payload).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert attendance_logs failed: {str(e)}")

    return RecognizeResponse(
        employee_id=employee_id if recognized else None,
        similarity=similarity,
        recognized=recognized,
    )
