from __future__ import annotations
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from api.supabase_client import get_supabase
from api.schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse,
)

router = APIRouter(prefix="/employees", tags=["employees"])


def _err(resp, msg: str):
    if resp.error:
        raise HTTPException(500, f"{msg}: {resp.error}")


@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    q: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = 200,
):
    sb = get_supabase()
    qy = sb.table("employees").select("*").limit(limit)

    if is_active is not None:
        qy = qy.eq("is_active", is_active)

    if q:
        qy = qy.or_(f"name.ilike.%{q}%,employee_code.ilike.%{q}%")

    resp = qy.execute()
    _err(resp, "list employees")
    return resp.data or []


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int):
    sb = get_supabase()
    resp = (
        sb.table("employees")
        .select("*")
        .eq("employee_id", employee_id)
        .maybe_single()
        .execute()
    )
    _err(resp, "get employee")
    if not resp.data:
        raise HTTPException(404, "Employee not found")
    return resp.data


@router.post("", response_model=EmployeeResponse)
def create_employee(body: EmployeeCreateRequest):
    sb = get_supabase()
    resp = sb.table("employees").insert(body.model_dump(exclude_none=True)).execute()
    _err(resp, "create employee")
    return resp.data[0]


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, body: EmployeeUpdateRequest):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(400, "No update fields")

    sb = get_supabase()
    resp = (
        sb.table("employees")
        .update(data)
        .eq("employee_id", employee_id)
        .execute()
    )
    _err(resp, "update employee")
    if not resp.data:
        raise HTTPException(404, "Employee not found")
    return resp.data[0]


@router.delete("/{employee_id}")
def delete_employee(employee_id: int):
    sb = get_supabase()
    resp = sb.table("employees").delete().eq("employee_id", employee_id).execute()
    _err(resp, "delete employee")
    if not resp.data:
        raise HTTPException(404, "Employee not found")
    return {"ok": True}
