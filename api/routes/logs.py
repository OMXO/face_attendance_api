from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.supabase_client import get_supabase

router = APIRouter(prefix="/logs", tags=["logs"])


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


class LogResponse(BaseModel):
    log_id: int
    employee_id: int
    event_type: str
    camera_id: Optional[str] = None
    score: Optional[float] = None
    created_at: Optional[str] = None


@router.get("")
def list_logs(
    limit: int = Query(default=200, ge=1, le=500),
    employee_id: Optional[int] = Query(default=None),
) -> Any:
    sb = get_supabase()

    q = sb.table("attendance_logs").select("*").order("created_at", desc=True).limit(limit)
    if employee_id is not None:
        q = q.eq("employee_id", employee_id)

    resp = q.execute()
    _raise_if_error(resp, "Failed to list logs")
    return resp.data or []
