import os
import traceback
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import RecognizeResponse
from api.embedding import get_embedding_from_image_bytes
from api.supabase_client import get_supabase
from api.routes import employees, faces, logs, cameras

load_dotenv()

app = FastAPI(title="Face Attendance API")

# CORS: allow Streamlit/local and broad access for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(employees.router)
app.include_router(faces.router)
app.include_router(logs.router)
app.include_router(cameras.router)


def vec_to_pgvector_str(v: np.ndarray) -> str:
    v = v.astype(np.float32).tolist()
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"


@app.get("/")
def root() -> Dict[str, Any]:
    return {"ok": True, "service": "face-attendance-api"}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


@app.post("/recognize", response_model=RecognizeResponse)
async def recognize(
    file: UploadFile = File(...),
    event_type: str = Form(...),
    camera_id: str = Form(""),
) -> RecognizeResponse:
    """
    Recognize a face from an uploaded image.
    Returns matched employee info and logs to DB.
    """
    try:
        img_bytes = await file.read()
        embedding = get_embedding_from_image_bytes(img_bytes)

        supabase = get_supabase()

        # Fetch all embeddings from DB (simple baseline approach)
        resp = supabase.table("faces").select("employee_id, embedding").execute()
        if getattr(resp, "error", None):
            raise HTTPException(status_code=500, detail=str(resp.error))

        rows = resp.data or []
        if not rows:
            return RecognizeResponse(
                ok=False,
                matched=False,
                message="No enrolled faces found in DB.",
            )

        # Compute cosine similarity (normalized embeddings)
        q = embedding.astype(np.float32)
        q = q / (np.linalg.norm(q) + 1e-9)

        best_id = None
        best_score = -1.0

        for r in rows:
            eid = r.get("employee_id")
            emb_str = r.get("embedding")

            # embedding stored as pgvector string like [0.1,0.2,...]
            if not emb_str:
                continue
            emb_str = emb_str.strip()
            if emb_str.startswith("[") and emb_str.endswith("]"):
                emb_str = emb_str[1:-1]
            try:
                vec = np.array([float(x) for x in emb_str.split(",")], dtype=np.float32)
            except Exception:
                continue

            vec = vec / (np.linalg.norm(vec) + 1e-9)
            score = float(np.dot(q, vec))
            if score > best_score:
                best_score = score
                best_id = eid

        # threshold (tune)
        threshold = float(os.getenv("MATCH_THRESHOLD", "0.35"))
        matched = best_id is not None and best_score >= threshold

        if not matched:
            return RecognizeResponse(
                ok=True,
                matched=False,
                score=best_score,
                message="No match.",
            )

        # Fetch employee info
        emp_resp = supabase.table("employees").select("*").eq("employee_id", best_id).single().execute()
        if getattr(emp_resp, "error", None):
            raise HTTPException(status_code=500, detail=str(emp_resp.error))
        emp = emp_resp.data or {}

        # Insert log
        log_payload = {
            "employee_id": best_id,
            "event_type": event_type,
            "camera_id": camera_id,
            "score": best_score,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        log_resp = supabase.table("attendance_logs").insert(log_payload).execute()
        if getattr(log_resp, "error", None):
            raise HTTPException(status_code=500, detail=str(log_resp.error))

        return RecognizeResponse(
            ok=True,
            matched=True,
            employee_id=best_id,
            employee_code=emp.get("employee_code"),
            name=emp.get("name"),
            event_type=event_type,
            camera_id=camera_id,
            score=best_score,
            message="Matched.",
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"recognize failed: {e}")
