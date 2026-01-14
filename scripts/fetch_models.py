# scripts/fetch_models.py
from __future__ import annotations

import hashlib
import os
import pathlib
import sys
import urllib.request


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")

    print(f"[models] downloading: {url}")
    with urllib.request.urlopen(url) as r, tmp.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    tmp.replace(dst)
    print(f"[models] saved: {dst} ({dst.stat().st_size / (1024*1024):.2f} MB)")


def ensure(name: str, url_env: str, sha_env: str | None, out_path: pathlib.Path) -> None:
    url = os.getenv(url_env, "").strip()
    if not url:
        raise RuntimeError(f"Missing env: {url_env}")

    expected_sha = os.getenv(sha_env, "").strip() if sha_env else ""
    if out_path.exists() and out_path.stat().st_size > 0:
        if expected_sha:
            got = sha256_file(out_path)
            if got.lower() == expected_sha.lower():
                print(f"[models] ok (cached): {name}")
                return
            print(f"[models] sha mismatch -> re-download: {name}")
        else:
            print(f"[models] exists (no sha check): {name}")
            return

    download(url, out_path)

    if expected_sha:
        got = sha256_file(out_path)
        if got.lower() != expected_sha.lower():
            raise RuntimeError(f"SHA256 mismatch for {name}: got={got}, expected={expected_sha}")
        print(f"[models] sha ok: {name}")


def main() -> int:
    base = pathlib.Path(os.getenv("MODEL_DIR", "models/ai"))

    ensure(
        name="arcface.onnx",
        url_env="ARCFACE_URL",
        sha_env="ARCFACE_SHA256",
        out_path=base / "arcface.onnx",
    )
    ensure(
        name="retinaface.onnx",
        url_env="RETINAFACE_URL",
        sha_env="RETINAFACE_SHA256",
        out_path=base / "retinaface.onnx",
    )
    print("[models] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
