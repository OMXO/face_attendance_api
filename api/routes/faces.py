# api/routes/faces.py
from __future__ import annotations

from typing import Any, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from api.embedding import get_embedding_from_image_bytes
from api.supabase_client import get_supabase

router = APIRouter(prefix="/faces", tags=["faces"])


# -----------------------------
# Helpers
# -----------------------------
def vec_to_pgvector_str(v: np.ndarray) -> str:
    """
    pgvector용 문자열 포맷: [0.123,0.456,...]
    """
    v = v.astype(np.float32).tolist()
    return "[" + ",".join(f"{x:.8f}" for x in v) + "]"


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


# -----------------------------
# Schemas
# -----------------------------
class FaceEnrollResponse(BaseModel):
    ok: bool
    employee_id: int
    message: Optional[str] = None


class FaceEmbeddingRow(BaseModel):
    employee_id: int
    embedding_dim: int = 512
    model_name: Optional[str] = None
    model_version: Optional[str] = None


# -----------------------------
# Routes
# -----------------------------
@router.post("/enroll/{employee_id}", response_model=FaceEnrollResponse)
async def enroll_face(
    employee_id: int,
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(default=None),      # ✅ FIX: Field -> Form
    model_version: Optional[str] = Form(default=None),   # ✅ FIX: Field -> Form
) -> FaceEnrollResponse:
    """
    얼굴 이미지 업로드 → 임베딩 생성 → face_embeddings에 UPSERT
    - face_embeddings PK가 employee_id라서 한 직원당 1개 임베딩을 유지.
    """
    sb = get_supabase()
    try:
        img_bytes = await file.read()
        emb = get_embedding_from_image_bytes(img_bytes)
        emb_str = vec_to_pgvector_str(emb)

        payload = {
            "employee_id": employee_id,
            "embedding_dim": int(emb.shape[0]) if hasattr(emb, "shape") else 512,
            "model_name": model_name,
            "model_version": model_version,
            "embedding": emb_str,
        }

        resp = (
            sb.table("face_embeddings")
            .upsert(payload, on_conflict="employee_id")
            .execute()
        )
        _raise_if_error(resp, "Failed to enroll face (upsert face_embeddings)")

        return FaceEnrollResponse(ok=True, employee_id=employee_id, message="enrolled")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"enroll_face failed: {e}")


@router.get("", response_model=list[FaceEmbeddingRow])
def list_faces(limit: int = 200) -> Any:
    """
    등록된 얼굴(임베딩) 목록
    """
    sb = get_supabase()
    resp = (
        sb.table("face_embeddings")
        .select("employee_id, embedding_dim, model_name, model_version")
        .limit(limit)
        .execute()
    )
    _raise_if_error(resp, "Failed to list faces (face_embeddings)")
    return resp.data or []


@router.delete("/{employee_id}")
def delete_face(employee_id: int) -> Any:
    """
    face_embeddings는 employee_id가 PK이므로 employee_id 기준으로 삭제
    """
    sb = get_supabase()
    resp = sb.table("face_embeddings").delete().eq("employee_id", employee_id).execute()
    _raise_if_error(resp, "Failed to delete face (face_embeddings)")
    return {"ok": True, "deleted_employee_id": employee_id}
