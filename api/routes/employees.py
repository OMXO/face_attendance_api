from __future__ import annotations

from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.supabase_client import get_supabase

router = APIRouter(prefix="/employees", tags=["employees"])


# -----------------------------
# Schemas
# -----------------------------
class EmployeeCreateRequest(BaseModel):
    employee_code: Optional[str] = Field(
        default=None, description="Employee visible code (e.g., EMP001)"
    )
    name: str = Field(..., min_length=1)
    is_active: bool = True


class EmployeeResponse(BaseModel):
    employee_id: int
    employee_code: Optional[str] = None
    name: str
    is_active: bool = True
    role: Optional[str] = None
    updated_at: Optional[str] = None
    has_face: bool = False


# -----------------------------
# Helpers
# -----------------------------
def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


# -----------------------------
# Routes
# -----------------------------
@router.get("")
def list_employees(
    query: str = Query(default="", description="Search by name or code"),
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    sb = get_supabase()

    q = sb.table("employees").select("*").limit(limit)
    if query:
        # try name ilike OR employee_code ilike (Supabase doesn't support OR easily in python client)
        # Using filter as a fallback: prefer name match
        q = q.ilike("name", f"%{query}%")

    resp = q.execute()
    _raise_if_error(resp, "Failed to list employees")

    employees = resp.data or []

    # attach has_face flag by checking faces table
    emp_ids = [e.get("employee_id") for e in employees if e.get("employee_id") is not None]
    face_map = set()
    if emp_ids:
        face_resp = sb.table("faces").select("employee_id").in_("employee_id", emp_ids).execute()
        if not getattr(face_resp, "error", None):
            face_map = {r.get("employee_id") for r in (face_resp.data or [])}

    for e in employees:
        e["has_face"] = e.get("employee_id") in face_map

    return employees


@router.post("")
def create_employee(req: EmployeeCreateRequest) -> Any:
    sb = get_supabase()
    payload = req.model_dump()

    resp = sb.table("employees").insert(payload).execute()
    _raise_if_error(resp, "Failed to create employee")
    return (resp.data or [{}])[0]


@router.get("/{employee_id}")
def get_employee(employee_id: int) -> Any:
    sb = get_supabase()
    resp = sb.table("employees").select("*").eq("employee_id", employee_id).single().execute()
    _raise_if_error(resp, "Failed to get employee")
    emp = resp.data or {}

    # has_face
    face_resp = sb.table("faces").select("employee_id").eq("employee_id", employee_id).execute()
    if not getattr(face_resp, "error", None):
        emp["has_face"] = bool(face_resp.data)

    return emp


@router.patch("/{employee_id}")
def update_employee(employee_id: int, patch: dict) -> Any:
    sb = get_supabase()
    resp = sb.table("employees").update(patch).eq("employee_id", employee_id).execute()
    _raise_if_error(resp, "Failed to update employee")
    return (resp.data or [{}])[0]
