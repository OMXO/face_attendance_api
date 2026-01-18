from __future__ import annotations

import os
import requests
import json
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN", "").strip()

class ApiError(RuntimeError):
    pass

def _headers() -> Dict[str, str]:
    h: Dict[str, str] = {}
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h

def _base(api_base: Optional[str]) -> str:
    b = (api_base or DEFAULT_API_BASE).rstrip("/")
    if not b:
        b = "http://127.0.0.1:8000"
    return b

def _try_urls(method: str, urls: List[str], *, timeout: float = 30, **kwargs) -> Any:
    last_err: Optional[str] = None
    for url in urls:
        try:
            r = requests.request(
                method,
                url,
                headers=_headers(),
                timeout=timeout,
                **kwargs,
            )
            if r.status_code < 400:
                ctype = (r.headers.get("content-type") or "").lower()
                return r.json() if "application/json" in ctype else r.text
            last_err = f"{r.status_code} {r.text[:300]}"
        except Exception as e:
            last_err = str(e)

    raise ApiError(f"API call failed. Tried: {urls}\nLast error: {last_err}")

def _wrap_recognize_response(res: Any) -> Dict[str, Any]:
    if not isinstance(res, dict):
        return {"recognized": False, "message": str(res)}

    recognized = bool(res.get("recognized", res.get("matched", False)))
    similarity = res.get("similarity", res.get("score", None))

    out = dict(res)
    out["recognized"] = recognized
    out["similarity"] = similarity
    return out

# ------------------------------------------------------------
# Employees
# ------------------------------------------------------------
def list_employees(query: str = "", limit: int = 50, api_base: str = "") -> List[Dict[str, Any]]:
    b = _base(api_base)
    url = f"{b}/employees"
    params = {"limit": limit, "query": query}
    res = _try_urls("GET", [url], params=params)
    if isinstance(res, list):
        return res
    return []

def create_employee(name: str, employee_code: Optional[str] = None, role: Optional[str] = None, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/employees"
    payload = {"name": name}
    if employee_code:
        payload["employee_code"] = employee_code
    if role:
        payload["role"] = role
    res = _try_urls("POST", [url], json=payload)
    return res if isinstance(res, dict) else {"result": res}

def update_employee(employee_id: int, name: Optional[str] = None, employee_code: Optional[str] = None, is_active: Optional[bool] = None, role: Optional[str] = None, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/employees/{employee_id}"
    payload: Dict[str, Any] = {}
    if name is not None: payload["name"] = name
    if employee_code is not None: payload["employee_code"] = employee_code
    if is_active is not None: payload["is_active"] = is_active
    if role is not None: payload["role"] = role
    res = _try_urls("PATCH", [url], json=payload)
    return res if isinstance(res, dict) else {"result": res}

def delete_employee(employee_id: int, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/employees/{employee_id}"
    res = _try_urls("DELETE", [url])
    return res if isinstance(res, dict) else {"result": res}

# ------------------------------------------------------------
# Faces
# ------------------------------------------------------------
def enroll_face(employee_id: int, image_bytes: bytes, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/faces/enroll/{employee_id}"
    files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
    res = _try_urls("POST", [url], files=files, timeout=60)
    return res if isinstance(res, dict) else {"result": res}

def delete_face(employee_id: int, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/faces/{employee_id}"
    res = _try_urls("DELETE", [url])
    return res if isinstance(res, dict) else {"result": res}

def check_face_duplicate(image_bytes: bytes, api_base: str = "") -> bool:
    b = _base(api_base)
    url = f"{b}/faces/check-duplicate"
    files = {"image": ("face.jpg", image_bytes, "image/jpeg")}
    try:
        res = _try_urls("POST", [url], files=files, timeout=60)
        return bool(res.get("duplicate")) if isinstance(res, dict) else False
    except Exception:
        return False

# ------------------------------------------------------------
# Logs
# ------------------------------------------------------------
def fetch_logs(limit: int = 50, api_base: str = "") -> List[Dict[str, Any]]:
    b = _base(api_base)
    url = f"{b}/logs"
    res = _try_urls("GET", [url], params={"limit": limit})
    if isinstance(res, list):
        return res
    return []

# ------------------------------------------------------------
# Cameras
# ------------------------------------------------------------
def list_cameras(limit: int = 50, api_base: str = "") -> List[Dict[str, Any]]:
    b = _base(api_base)
    url = f"{b}/cameras"
    res = _try_urls("GET", [url], params={"limit": limit})
    if isinstance(res, list):
        return res
    return []

# ------------------------------------------------------------
# Health
# ------------------------------------------------------------
def health(api_base: str = "") -> bool:
    b = _base(api_base)
    url = f"{b}/health"
    try:
        r = requests.get(url, headers=_headers(), timeout=5)
        return r.status_code < 400
    except Exception:
        return False

# ------------------------------------------------------------
# Recognize
# ------------------------------------------------------------
def recognize(image_bytes: bytes, event_type: str, camera_id: str, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/recognize"
    files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
    data = {"event_type": event_type, "camera_id": camera_id}
    res = _try_urls("POST", [url], files=files, data=data, timeout=60)
    return _wrap_recognize_response(res)
