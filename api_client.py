# UI/api_client.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN", "").strip()  # 있으면 사용, 없으면 빈값


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
            r = requests.request(method, url, headers=_headers(), timeout=timeout, **kwargs)
            if r.status_code < 400:
                ctype = (r.headers.get("content-type") or "").lower()
                return r.json() if "application/json" in ctype else r.text
            last_err = f"{r.status_code} {r.text[:300]}"
        except Exception as e:
            last_err = str(e)
    raise ApiError(f"API call failed. Tried: {urls}\nLast error: {last_err}")


def _wrap_recognize_response(res: Any) -> Dict[str, Any]:
    """
    UI는 recognized/similarity를 기대하는데(현재 UI 코드) :contentReference[oaicite:3]{index=3}
    백엔드는 matched/score 형태일 가능성이 높아서(현재 api/main.py) :contentReference[oaicite:4]{index=4}
    여기서 UI 호환 형태로 매핑.
    """
    if not isinstance(res, dict):
        return {"recognized": False, "message": str(res)}

    recognized = bool(res.get("recognized", res.get("matched", False)))
    similarity = res.get("similarity", res.get("score", None))

    out = dict(res)
    out["recognized"] = recognized
    out["similarity"] = similarity
    return out


# -------------------------
# Public API for UI pages
# -------------------------
def list_employees(query: str = "", limit: int = 50, api_base: str = "") -> List[Dict[str, Any]]:
    b = _base(api_base)
    url = f"{b}/employees"
    res = _try_urls("GET", [url], params={"query": query, "limit": limit})
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and isinstance(res.get("data"), list):
        return res["data"]
    return []


def create_employee(name: str, employee_code: Optional[str] = None, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/employees"
    payload: Dict[str, Any] = {"name": name}
    if employee_code:
        payload["employee_code"] = employee_code
    res = _try_urls("POST", [url], json=payload)
    return res if isinstance(res, dict) else {"result": res}


def enroll_face(employee_id: int, image_bytes: bytes, api_base: str = "") -> Dict[str, Any]:
    """
    백엔드 구현마다 경로가 달라서 둘 다 시도:
    - /faces/enroll/{id}  (현재 api/routes/faces.py 패턴)
    - /employees/{id}/enroll-face (대체 패턴)
    """
    b = _base(api_base)
    files = {"file": ("face.jpg", image_bytes, "image/jpeg")}
    urls = [
        f"{b}/faces/enroll/{employee_id}",
        f"{b}/employees/{employee_id}/enroll-face",
    ]
    res = _try_urls("POST", urls, files=files, timeout=60)
    return res if isinstance(res, dict) else {"result": res}


def fetch_logs(limit: int = 200, api_base: str = "") -> List[Dict[str, Any]]:
    b = _base(api_base)
    url = f"{b}/logs"
    res = _try_urls("GET", [url], params={"limit": limit})
    if isinstance(res, list):
        return res
    if isinstance(res, dict) and isinstance(res.get("data"), list):
        return res["data"]
    return []


def recognize(image_bytes: bytes, event_type: str, camera_id: str, api_base: str = "") -> Dict[str, Any]:
    b = _base(api_base)
    url = f"{b}/recognize"
    files = {"file": ("frame.jpg", image_bytes, "image/jpeg")}
    data = {"event_type": event_type, "camera_id": camera_id}
    res = _try_urls("POST", [url], files=files, data=data, timeout=60)
    return _wrap_recognize_response(res)
