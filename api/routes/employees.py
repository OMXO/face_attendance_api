# api/routes/employees.py
from __future__ import annotations

from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from api.supabase_client import get_supabase

router = APIRouter(prefix="/employees", tags=["employees"])


class EmployeeCreateRequest(BaseModel):
    employee_code: Optional[str] = Field(default=None, description="Employee visible code (e.g., EMP001)")
    name: str = Field(..., min_length=1)
    is_active: bool = True


def _raise_if_error(resp: Any, msg: str) -> None:
    err = getattr(resp, "error", None)
    if err:
        raise HTTPException(status_code=500, detail=f"{msg}: {err}")


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # pydantic v2
    return model.dict()  # pydantic v1


@router.get("")
def list_employees(
    query: str = Query(default="", description="Search by name or code"),
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    sb = get_supabase()

    q = sb.table("employees").select("*").limit(limit)
    if query:
        # 기존 코드는 name만 ilike였는데, code도 같이 검색되면 UI가 더 편함
        q = q.or_(f"name.ilike.%{query}%,employee_code.ilike.%{query}%")

    resp = q.execute()
    _raise_if_error(resp, "Failed to list employees")
    employees = resp.data or []

    # attach has_face flag by checking face_embeddings table
    emp_ids = [e.get("employee_id") for e in employees if e.get("employee_id") is not None]
    face_map = set()

    if emp_ids:
        face_resp = (
            sb.table("face_embeddings")
            .select("employee_id")
            .in_("employee_id", emp_ids)
            .execute()
        )
        if not getattr(face_resp, "error", None):
            face_map = {r.get("employee_id") for r in (face_resp.data or [])}

    for e in employees:
        e["has_face"] = e.get("employee_id") in face_map

    return employees


@router.post("")
def create_employee(req: EmployeeCreateRequest) -> Any:
    sb = get_supabase()
    payload = _model_to_dict(req)

    resp = sb.table("employees").insert(payload).execute()
    _raise_if_error(resp, "Failed to create employee")
    return (resp.data or [{}])[0]


@router.get("/{employee_id}")
def get_employee(employee_id: int) -> Any:
    sb = get_supabase()
    resp = sb.table("employees").select("*").eq("employee_id", employee_id).single().execute()
    _raise_if_error(resp, "Failed to get employee")
    emp = resp.data or {}

    face_resp = sb.table("face_embeddings").select("employee_id").eq("employee_id", employee_id).execute()
    if not getattr(face_resp, "error", None):
        emp["has_face"] = bool(face_resp.data)

    return emp


@router.patch("/{employee_id}")
def update_employee(employee_id: int, patch: Dict[str, Any]) -> Any:
    sb = get_supabase()
    resp = sb.table("employees").update(patch).eq("employee_id", employee_id).execute()
    _raise_if_error(resp, "Failed to update employee")
    return (resp.data or [{}])[0]


@router.post("/{employee_id}/enroll-face")
async def enroll_face_compat(employee_id: int, file: UploadFile = File(...)) -> Any:
    """
    UI 호환 엔드포인트:
    /employees/{id}/enroll-face -> /faces/enroll/{id}
    """
    from api.routes.faces import enroll_face  # local import
    return await enroll_face(employee_id, file)
