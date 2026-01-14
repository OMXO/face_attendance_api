from __future__ import annotations
from typing import Any, List

from fastapi import APIRouter, HTTPException
from api.supabase_client import get_supabase

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _err(resp, msg: str):
    if resp.error:
        raise HTTPException(500, f"{msg}: {resp.error}")


@router.get("")
def list_schedules() -> List[Any]:
    sb = get_supabase()
    resp = sb.table("schedules").select("*").execute()
    _err(resp, "list schedules")
    return resp.data or []


@router.post("")
def create_schedule(
    employee_id: int,
    schedule: str,
    start_time: str,
    end_time: str,
):
    sb = get_supabase()
    resp = sb.table("schedules").insert(
        {
            "employee_id": employee_id,
            "schedule": schedule,
            "start_time": start_time,
            "end_time": end_time,
        }
    ).execute()
    _err(resp, "create schedule")
    return resp.data[0]


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int):
    sb = get_supabase()
    resp = sb.table("schedules").delete().eq("schedule_id", schedule_id).execute()
    _err(resp, "delete schedule")
    if not resp.data:
        raise HTTPException(404, "Schedule not found")
    return {"ok": True}
