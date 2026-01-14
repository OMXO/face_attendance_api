from __future__ import annotations
from typing import Any, List

from fastapi import APIRouter, HTTPException, UploadFile, File
from api.supabase_client import get_supabase
from api.embedding import get_embedding_from_image_bytes

router = APIRouter(prefix="/faces", tags=["faces"])


def _err(resp, msg: str):
    if resp.error:
        raise HTTPException(500, f"{msg}: {resp.error}")


@router.get("")
def list_faces(limit: int = 200) -> List[Any]:
    sb = get_supabase()
    resp = sb.table("face_embeddings").select("*").limit(limit).execute()
    _err(resp, "list faces")
    return resp.data or []


@router.get("/{employee_id}")
def get_face(employee_id: int):
    sb = get_supabase()
    resp = (
        sb.table("face_embeddings")
        .select("*")
        .eq("employee_id", employee_id)
        .maybe_single()
        .execute()
    )
    _err(resp, "get face")
    if not resp.data:
        raise HTTPException(404, "Face not found")
    return resp.data


@router.post("/enroll/{employee_id}")
async def enroll_face(employee_id: int, file: UploadFile = File(...)):
    img = await file.read()
    if not img:
        raise HTTPException(400, "Empty image")

    emb = get_embedding_from_image_bytes(img)

    sb = get_supabase()
    body = {
        "employee_id": employee_id,
        "embedding_dim": 512,
        "model_name": "arcface",
        "model_version": "onnx",
        "embedding": emb,
    }
    resp = sb.table("face_embeddings").upsert(body).execute()
    _err(resp, "enroll face")

    return {"ok": True, "employee_id": employee_id}


@router.delete("/{employee_id}")
def delete_face(employee_id: int):
    sb = get_supabase()
    resp = sb.table("face_embeddings").delete().eq("employee_id", employee_id).execute()
    _err(resp, "delete face")
    if not resp.data:
        raise HTTPException(404, "Face not found")
    return {"ok": True}
