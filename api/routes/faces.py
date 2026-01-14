from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from api.embedding import get_embedding_from_image_bytes
from api.supabase_client import get_supabase

router = APIRouter(prefix="/faces", tags=["faces"])


def vec_to_pgvector_str(v: np.ndarray) -> str:
    v = v.astype(np.float32).tolist()
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


class FaceEnrollResponse(BaseModel):
    ok: bool
    employee_id: int
    face_id: Optional[int] = None
    message: Optional[str] = None


@router.post("/enroll/{employee_id}", response_model=FaceEnrollResponse)
async def enroll_face(employee_id: int, file: UploadFile = File(...)) -> FaceEnrollResponse:
    """
    Upload a face image for an employee and store embedding into DB.
    """
    sb = get_supabase()
    try:
        img_bytes = await file.read()
        emb = get_embedding_from_image_bytes(img_bytes)
        emb_str = vec_to_pgvector_str(emb)

        payload = {
            "employee_id": employee_id,
            "embedding": emb_str,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        resp = sb.table("faces").insert(payload).execute()
        _raise_if_error(resp, "Failed to enroll face")
        row = (resp.data or [{}])[0]
        face_id = row.get("face_id") or row.get("id")
        return FaceEnrollResponse(ok=True, employee_id=employee_id, face_id=face_id, message="enrolled")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"enroll_face failed: {e}")


@router.get("")
def list_faces(limit: int = 200) -> Any:
    sb = get_supabase()
    resp = sb.table("faces").select("face_id, employee_id, created_at").limit(limit).execute()
    _raise_if_error(resp, "Failed to list faces")
    return resp.data or []


@router.delete("/{face_id}")
def delete_face(face_id: int) -> Any:
    sb = get_supabase()
    resp = sb.table("faces").delete().eq("face_id", face_id).execute()
    _raise_if_error(resp, "Failed to delete face")
    return {"ok": True, "deleted": face_id}
