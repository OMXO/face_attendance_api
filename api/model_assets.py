# api/model_assets.py
import os
from pathlib import Path
import urllib.request

ARC_URL = os.getenv("ARC_MODEL_URL", "")
RETINA_URL = os.getenv("RETINA_MODEL_URL", "")
MODELS_DIR = Path(os.getenv("MODELS_DIR", "/tmp/models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

ARC_PATH = MODELS_DIR / "arcface.onnx"
RETINA_PATH = MODELS_DIR / "retinaface.onnx"

def _download(url: str, out: Path):
    if not url:
        raise RuntimeError(f"Missing URL for {out.name}")
    tmp = out.with_suffix(out.suffix + ".download")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(out)

def ensure_models():
    if not ARC_PATH.exists():
        _download(ARC_URL, ARC_PATH)
    if not RETINA_PATH.exists():
        _download(RETINA_URL, RETINA_PATH)
