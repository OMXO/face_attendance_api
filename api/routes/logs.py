# api/routes/logs.py
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.supabase_client import get_supabase

router = APIRouter(prefix="/logs", tags=["logs"])


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


class LogRow(BaseModel):
    log_id: int
    event_time: str
    event_type: str
    camera_id: str
    recognized: bool
    similarity: Optional[float] = None
    employee_id: Optional[int] = None
    created_at: str


@router.get("", response_model=list[LogRow])
def list_logs(
    limit: int = Query(default=200, ge=1, le=500),
    employee_id: Optional[int] = Query(default=None),
) -> Any:
    sb = get_supabase()

    q = (
        sb.table("attendance_logs")
        .select("log_id,event_time,event_type,camera_id,recognized,similarity,employee_id,created_at")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if employee_id is not None:
        q = q.eq("employee_id", employee_id)

    resp = q.execute()
    _raise_if_error(resp, "Failed to list logs")
    return resp.data or []
