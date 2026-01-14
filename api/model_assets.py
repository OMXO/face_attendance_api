# api/model_assets.py
from __future__ import annotations

import os
import urllib.request
from pathlib import Path
import tempfile

# ✅ 키 이름을 확실히 고정 + 혹시 예전 키가 있으면 fallback
ARC_URL = (
    os.getenv("ARC_MODEL_URL", "").strip()
    or os.getenv("ARC_URL", "").strip()
)
RETINA_URL = (
    os.getenv("RETINA_MODEL_URL", "").strip()
    or os.getenv("RETINA_URL", "").strip()
)

# ✅ MODELS_DIR도 cross-platform 안전하게
# - Render/Linux: /tmp/models 권장
# - Windows 로컬: /tmp/models는 애매하니까 기본은 시스템 temp 밑으로
_default_dir = Path(tempfile.gettempdir()) / "face_attendance_models"
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(_default_dir))).resolve()
MODELS_DIR.mkdir(parents=True, exist_ok=True)

ARC_PATH = MODELS_DIR / "arcface.onnx"
RETINA_PATH = MODELS_DIR / "retinaface.onnx"


def _download(url: str, out_path: Path) -> None:
    if not url:
        raise RuntimeError(f"Missing URL for {out_path.name}")

    tmp = out_path.with_suffix(out_path.suffix + ".download")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(out_path)


def ensure_models() -> dict:
    # 디버그: 지금 어떤 값으로 들어오는지 확정
    print("[model_assets] MODELS_DIR =", MODELS_DIR)
    print("[model_assets] ARC_URL set?   =", bool(ARC_URL))
    print("[model_assets] RETINA_URL set?=", bool(RETINA_URL))

    if not ARC_PATH.exists():
        _download(ARC_URL, ARC_PATH)
    if not RETINA_PATH.exists():
        _download(RETINA_URL, RETINA_PATH)

    return {"arcface": str(ARC_PATH), "retinaface": str(RETINA_PATH)}
