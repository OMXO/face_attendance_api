from __future__ import annotations

from typing import Optional
import numpy as np

import cv2

from models.face_models import load_retinaface, load_arcface

# Lazy-loaded models
_RETINA = None
_ARCFACE = None


def _ensure_models():
    global _RETINA, _ARCFACE
    if _RETINA is None:
        _RETINA = load_retinaface()
    if _ARCFACE is None:
        _ARCFACE = load_arcface()


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes.")
    return img


def _crop_face(img_bgr: np.ndarray) -> np.ndarray:
    """
    Detect face using RetinaFace and crop the most confident face.
    """
    _ensure_models()

    # RetinaFace expected RGB or BGR depending on implementation inside face_models
    # Keep as BGR here; face_models should handle conversion.
    bboxes, landmarks = _RETINA.detect(img_bgr)
    if bboxes is None or len(bboxes) == 0:
        raise ValueError("No face detected.")

    # choose best score
    best = max(bboxes, key=lambda x: float(x[4]) if len(x) > 4 else 0.0)
    x1, y1, x2, y2 = [int(v) for v in best[:4]]

    h, w = img_bgr.shape[:2]
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid face bbox.")

    face = img_bgr[y1:y2, x1:x2]
    return face


def _preprocess_for_arcface(face_bgr: np.ndarray) -> np.ndarray:
    """
    ArcFace commonly expects 112x112 RGB, normalized.
    """
    face = cv2.resize(face_bgr, (112, 112))
    face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    # normalize to [-1, 1] or [0,1] depends on arcface model implementation
    # We'll keep float32 [0,1] here; face_models should adapt if needed.
    face_rgb = face_rgb.astype(np.float32) / 255.0
    return face_rgb


def get_embedding_from_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Decode image -> detect+crop face -> ArcFace embedding
    """
    _ensure_models()
    img = _decode_image(image_bytes)
    face = _crop_face(img)
    x = _preprocess_for_arcface(face)

    emb = _ARCFACE.get_embedding(x)
    if emb is None:
        raise ValueError("Failed to get embedding.")
    emb = np.asarray(emb, dtype=np.float32).reshape(-1)
    return emb


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float(np.dot(a, b))
