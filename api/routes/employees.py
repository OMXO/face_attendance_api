from __future__ import annotations
from typing import List, Optional, Any
from fastapi import APIRouter, Query, HTTPException
from api.supabase_client import get_supabase
from api.common import execute_or_500, get_data, get_one_or_404
from api.schemas import EmployeeCreateRequest, EmployeeUpdateRequest, EmployeeResponse

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    query: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
):
    sb = get_supabase()

    def _run():
        q = sb.table("employees").select("*").limit(limit)
        if query:
            q = q.ilike("name", f"%{query}%")
        return q.execute()

    resp = execute_or_500(_run, "list employees")

    employees = get_data(resp)
    if not employees:
        return []

    emp_ids = [e["employee_id"] for e in employees]

    # 🔑 CORRECT FACE CHECK (fetch persons separately to avoid join errors)
    try:
        # Fetch persons who HAVE face embeddings
        # We check persons table for presence of any face_embeddings
        face_resp = sb.table("persons") \
            .select("employee_id, face_embeddings(id)") \
            .in_("employee_id", emp_ids) \
            .execute().data
        
        emp_with_faces = {
            int(p["employee_id"]) for p in face_resp if p.get("face_embeddings")
        }
    except Exception as e:
        print(f"⚠️ Face check failed: {e}")
        emp_with_faces = set()

    for e in employees:
        e["has_face"] = int(e["employee_id"]) in emp_with_faces

    return employees


@router.post("", response_model=EmployeeResponse)
def create_employee(body: EmployeeCreateRequest):
    sb = get_supabase()
    payload = body.model_dump(exclude_none=True)
    
    resp = execute_or_500(lambda: sb.table("employees").insert(payload).execute(), "create employee")
    return get_one_or_404(resp, "Failed to create employee")


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int):
    sb = get_supabase()
    resp = execute_or_500(
        lambda: sb.table("employees").select("*").eq("employee_id", employee_id).maybe_single().execute(),
        "get employee",
    )
    return get_one_or_404(resp, "Employee not found")


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, body: EmployeeUpdateRequest):
    sb = get_supabase()
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(400, "No fields to update")

    resp = execute_or_500(
        lambda: sb.table("employees").update(payload).eq("employee_id", employee_id).execute(),
        "update employee",
    )
    return get_one_or_404(resp, "Employee not found")


@router.delete("/{employee_id}")
def delete_employee(employee_id: int):
    sb = get_supabase()
    
    # Optional: Cleanup persons table if cascading is not set in DB
    # Based on previous logic, we might want to be careful here.
    # But usually, a hard delete of employee should cascade to persons -> faces if set in SQL.
    
    resp = execute_or_500(
        lambda: sb.table("employees").delete().eq("employee_id", employee_id).execute(),
        "delete employee",
    )
    if not get_data(resp):
        raise HTTPException(404, "Employee not found or already deleted")
    return {"ok": True}
