from __future__ import annotations
from typing import Any, List

from fastapi import APIRouter, HTTPException
from api.supabase_client import get_supabase

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _err(resp, msg: str):
    if resp.error:
        raise HTTPException(500, f"{msg}: {resp.error}")


@router.get("")
def list_cameras() -> List[Any]:
    sb = get_supabase()
    resp = sb.table("cameras").select("*").execute()
    _err(resp, "list cameras")
    return resp.data or []


@router.post("")
def create_camera(camera_id: str):
    sb = get_supabase()
    resp = sb.table("cameras").insert({"camera_id": camera_id}).execute()
    _err(resp, "create camera")
    return resp.data[0]


@router.patch("/{camera_id}")
def toggle_camera(camera_id: str, is_active: bool):
    sb = get_supabase()
    resp = (
        sb.table("cameras")
        .update({"is_active": is_active})
        .eq("camera_id", camera_id)
        .execute()
    )
    _err(resp, "update camera")
    return resp.data[0]


@router.delete("/{camera_id}")
def delete_camera(camera_id: str):
    sb = get_supabase()
    resp = sb.table("cameras").delete().eq("camera_id", camera_id).execute()
    _err(resp, "delete camera")
    if not resp.data:
        raise HTTPException(404, "Camera not found")
    return {"ok": True}
