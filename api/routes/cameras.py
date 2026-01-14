from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.supabase_client import get_supabase

router = APIRouter(prefix="/cameras", tags=["cameras"])


class CameraCreateRequest(BaseModel):
    camera_id: Optional[str] = Field(default=None, description="Human readable camera id")
    name: str = Field(..., min_length=1)
    is_active: bool = True


class CameraResponse(BaseModel):
    id: int
    camera_id: Optional[str] = None
    name: str
    is_active: bool = True
    updated_at: Optional[str] = None


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


@router.get("")
def list_cameras(limit: int = 100) -> Any:
    sb = get_supabase()
    resp = sb.table("cameras").select("*").limit(limit).execute()
    _raise_if_error(resp, "Failed to list cameras")
    return resp.data or []


@router.post("")
def create_camera(req: CameraCreateRequest) -> Any:
    sb = get_supabase()
    payload = req.model_dump()
    resp = sb.table("cameras").insert(payload).execute()
    _raise_if_error(resp, "Failed to create camera")
    return (resp.data or [{}])[0]


@router.patch("/{id}")
def update_camera(id: int, patch: Dict[str, Any]) -> Any:
    sb = get_supabase()
    resp = sb.table("cameras").update(patch).eq("id", id).execute()
    _raise_if_error(resp, "Failed to update camera")
    return (resp.data or [{}])[0]
