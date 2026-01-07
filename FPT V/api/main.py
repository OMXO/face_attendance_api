import os
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from api.supabase_client import get_supabase
from api.schemas import RecognizeResponse
from api.embedding import get_embedding_from_image_bytes

# ✅ routers import
from api.routes.employees import router as employees_router
from api.routes.cameras import router as cameras_router
from api.routes.logs import router as logs_router
from api.routes.faces import router as faces_router

load_dotenv()

# ✅ 1) app 먼저 생성
app = FastAPI(
    title="Face Attendance API",
    version="1.0.0",
)

# ✅ 2) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 3) routers mount는 app 생성 후
app.include_router(cameras_router, prefix="/cameras", tags=["cameras"])
app.include_router(employees_router, prefix="/employees", tags=["employees"])
app.include_router(logs_router, prefix="/logs", tags=["logs"])
app.include_router(faces_router, tags=["faces"])  # /employees/{id}/faces 형태면 prefix 불필요

# -----------------------------
# Helpers
# -----------------------------
def vec_to_pgvector_str(v: np.ndarray) -> str:
    v = v.astype(np.float32).tolist()
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"

# -----------------------------
# Root / Health
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
    camera_id: str | None = Form(default=None),
    event_type: str | None = Form(default=None),
):
    # ---- 파일 검증 ----
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Invalid content_type: {file.content_type}. Must be image/*")

    img_bytes = await file.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # camera_id / event_type (Streamlit에서 보내면 그걸 쓰고, 없으면 env fallback)
    cam = (camera_id or "").strip() or os.getenv("CAMERA_ID", "").strip()
    if not cam:
        raise HTTPException(status_code=400, detail="camera_id is required (form field) or set CAMERA_ID env var")

    evt = (event_type or "").strip() or os.getenv("DEFAULT_EVENT_TYPE", "CHECK_IN")
    if evt not in ("CHECK_IN", "CHECK_OUT"):
        raise HTTPException(status_code=400, detail="event_type must be CHECK_IN or CHECK_OUT")

    min_sim = float(os.getenv("MIN_SIMILARITY", "0.45"))

    # 1) 임베딩 생성
    try:
        emb = get_embedding_from_image_bytes(img_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    if emb.ndim != 1:
        raise HTTPException(status_code=500, detail="Embedding must be 1D vector")
    if emb.shape[0] != 512:
        raise HTTPException(status_code=500, detail=f"Embedding dim mismatch: got {emb.shape[0]}, expected 512")

    supabase = get_supabase()

    # 2) DB 매칭
    query_vec = vec_to_pgvector_str(emb)

    try:
        match = supabase.rpc(
            "match_face",
            {"query_embedding": query_vec, "min_similarity": min_sim}
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase RPC failed: {str(e)}")

    if not match.data:
        # 등록자 없거나 매칭 실패
        # 실패 로그도 남기고 싶으면 아래 insert 추가 가능
        return RecognizeResponse(employee_id=None, similarity=None, recognized=False)

    row = match.data[0]
    employee_id = row.get("employee_id")
    similarity = float(row.get("similarity", 0.0))
    recognized = bool(row.get("recognized", False))

    # 3) 출석 로그 기록
    log_payload = {
        "employee_id": employee_id if recognized else None,
        "camera_id": cam,
        "event_type": evt,
        "similarity": similarity,
        "recognized": recognized,
        "event_time": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase.table("attendance_logs").insert(log_payload).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert attendance_logs failed: {str(e)}")

    return RecognizeResponse(
        employee_id=employee_id if recognized else None,
        similarity=similarity,
        recognized=recognized
    )
