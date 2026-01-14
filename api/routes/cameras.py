# api/routes/cameras.py
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.supabase_client import get_supabase

router = APIRouter(prefix="/cameras", tags=["cameras"])


class CameraCreateRequest(BaseModel):
    camera_id: str = Field(..., description="Camera primary key (text)")
    is_active: bool = True

    # UI 호환용(DB에는 없음) - 들어와도 무시/호환 처리
    name: Optional[str] = None
    location: Optional[str] = None


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


def _decorate(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    DB에는 없는 필드를 응답에만 붙여서 UI가 기대하는 키를 유지
    """
    camera_id = row.get("camera_id")
    row["name"] = row.get("name") or camera_id          # fallback
    row["location"] = row.get("location") or None       # fallback
    return row


@router.get("")
def list_cameras(limit: int = 200) -> Any:
    sb = get_supabase()
    resp = sb.table("cameras").select("*").limit(limit).execute()
    _raise_if_error(resp, "Failed to list cameras")

    data = resp.data or []
    return [_decorate(r) for r in data]


@router.post("")
def create_camera(req: CameraCreateRequest) -> Any:
    sb = get_supabase()

    # DB에 실제 존재하는 컬럼만 insert
    payload = {"camera_id": req.camera_id, "is_active": req.is_active}

    resp = sb.table("cameras").insert(payload).execute()
    _raise_if_error(resp, "Failed to create camera")

    row = (resp.data or [{}])[0]
    return _decorate(row)


@router.patch("/{camera_id}")
def update_camera(camera_id: str, patch: Dict[str, Any]) -> Any:
    sb = get_supabase()

    # DB에 실제 존재하는 컬럼만 update 허용
    safe_patch = {k: v for k, v in patch.items() if k in {"is_active"}}

    resp = sb.table("cameras").update(safe_patch).eq("camera_id", camera_id).execute()
    _raise_if_error(resp, "Failed to update camera")

    row = (resp.data or [{}])[0]
    return _decorate(row)
