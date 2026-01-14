from pydantic import BaseModel
from typing import Optional


class RecognizeResponse(BaseModel):
    ok: bool
    matched: bool
    message: Optional[str] = None
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    name: Optional[str] = None
    event_type: Optional[str] = None
    camera_id: Optional[str] = None
    score: Optional[float] = None
