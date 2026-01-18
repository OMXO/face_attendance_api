from __future__ import annotations
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form
from typing import Dict

from api.supabase_client import get_supabase
from api.models.face_models import detect_faces, get_embedding, safe_crop

router = APIRouter(prefix="/recognize", tags=["recognition"])

# 🔑 CACHE: { emp_id: { "vec": ..., "name": ..., "code": ... } }
KNOWN: Dict[int, Dict] = {}


def refresh_embeddings():
    global KNOWN
    sb = get_supabase()

    # 1. Fetch face embeddings joined with persons
    # (persons -> face_embeddings should exist via person_id)
    rows = sb.table("face_embeddings") \
        .select("embedding, persons!inner(employee_id, name)") \
        .execute().data

    if not rows:
        KNOWN.clear()
        print("ℹ️ No embeddings found in database.")
        return

    # 2. Collect unique employee IDs (they might be strings in 'persons')
    emp_ids_raw = list({r["persons"]["employee_id"] for r in rows if r.get("persons")})
    
    # 3. Fetch employee codes from employees table
    # We fetch them separately to avoid join errors if foreign keys are missing
    emp_meta = {}
    try:
        emp_resp = sb.table("employees") \
            .select("employee_id, employee_code") \
            .in_("employee_id", emp_ids_raw) \
            .execute().data
        for e in emp_resp:
            emp_meta[str(e["employee_id"])] = e.get("employee_code")
    except Exception as e:
        print(f"⚠️ Could not fetch employee codes: {e}")

    # 4. Rebuild Cache
    KNOWN.clear()
    for r in rows:
        p = r.get("persons")
        if not p: continue
        
        raw_id = p["employee_id"]
        emp_id = int(raw_id)
        name = p.get("name") or "Unknown"
        code = emp_meta.get(str(raw_id)) or f"ID-{emp_id}"
        
        vec_str = r["embedding"].strip("[]")
        if not vec_str: continue
        
        vec = np.fromstring(vec_str, sep=",", dtype=np.float32)
        KNOWN[emp_id] = {
            "vec": vec / np.linalg.norm(vec),
            "name": name,
            "code": code
        }

    print(f"✅ Loaded {len(KNOWN)} embeddings with metadata")


@router.post("/")
async def recognize(
    image: UploadFile = File(...),
    event_type: str = Form(...),
    camera_id: str = Form(...),
):
    if not KNOWN:
        refresh_embeddings()

    img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    faces = detect_faces(img)

    if not faces:
        return {"recognized": False}

    faces.sort(key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)
    face = safe_crop(img, faces[0])
    emb = get_embedding(face)
    emb = emb / np.linalg.norm(emb)

    best_id, best_score = None, -1
    for eid, data in KNOWN.items():
        ref = data["vec"]
        s = float(np.dot(emb, ref))
        if s > best_score:
            best_id, best_score = eid, s

    is_recognized = best_score >= 0.38
    result = {
        "recognized": is_recognized,
        "employee_id": best_id,
        "similarity": round(best_score, 4),
    }

    if is_recognized and best_id in KNOWN:
        result["name"] = KNOWN[best_id]["name"]
        result["employee_code"] = KNOWN[best_id]["code"]

        # 🕒 LOG ATTENDANCE (Optional: call logs route or insert here)
        try:
            sb = get_supabase()
            sb.table("attendance_logs").insert({
                "employee_id": best_id,
                "camera_id": camera_id,
                "event_type": event_type,
                "recognized": True,
                "similarity": round(best_score, 4)
            }).execute()
        except Exception as e:
            print(f"❌ Failed to log attendance: {e}")

    return result
